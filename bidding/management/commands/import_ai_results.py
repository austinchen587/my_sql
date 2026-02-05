import csv
import json
import os
from django.core.management.base import BaseCommand
from bidding.models import ProcurementCommodityResult, BiddingProject
from emall.models import ProcurementEmall

class Command(BaseCommand):
    help = '导入 AI 推荐结果并提示测试链接'

    def handle(self, *args, **options):
        # 文件路径：默认在项目根目录
        file_path = 'procurement_commodity_result.txt'
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'❌ 找不到文件: {file_path}，请将其放在项目根目录(manage.py旁边)'))
            return

        self.stdout.write('🔄 开始导入 AI 推荐数据...')
        
        count = 0
        imported_procurement_ids = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 使用 DictReader 自动处理 CSV 格式（包括引号和逗号）
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # 获取原始采购 ID
                        procurement_id = int(row['procurement_id'])
                        
                        # 1. 安全检查：确保关联的原始项目存在
                        if not ProcurementEmall.objects.filter(id=procurement_id).exists():
                            # 如果主表里没这个项目，导入了也没用，跳过
                            continue

                        # 2. 创建或更新 AI 结果
                        # 使用 update_or_create 防止重复导入报错
                        ProcurementCommodityResult.objects.update_or_create(
                            id=row['id'], # 使用 CSV 里的 ID
                            defaults={
                                'procurement_id': procurement_id,
                                'brand_id': row['brand_id'] if row['brand_id'] else None,
                                'item_name': row['item_name'],
                                'specifications': row['specifications'],
                                'selected_suppliers': row['selected_suppliers'],
                                'selection_reason': row['selection_reason'],
                                'model_used': row['model_used'],
                                'created_at': row['created_at']
                            }
                        )
                        count += 1
                        imported_procurement_ids.append(procurement_id)
                        
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠️ 行导入失败: {e}'))

            self.stdout.write(self.style.SUCCESS(f'✅ 成功导入 {count} 条 AI 结果数据！'))

            # --- 关键步骤：告诉用户去哪里看效果 ---
            self.stdout.write('\n🔎 正在寻找可供测试的详情页链接...')
            
            # 查找一个既导入了 AI 数据，又在“竞价大厅(BiddingProject)”表里存在的项目
            test_project = BiddingProject.objects.filter(source_emall__id__in=imported_procurement_ids).first()
            
            if test_project:
                url = f"http://localhost:3000/bidding/detail/{test_project.id}"
                self.stdout.write(self.style.SUCCESS(f"\n🎉 找到了！请访问此链接查看效果:\n👉 {url}"))
                self.stdout.write(f"(对应的原始采购ID为: {test_project.source_emall.id})")
            else:
                self.stdout.write(self.style.WARNING("\n⚠️ 数据已导入，但在 '竞价大厅' 列表中没找到对应的项目。"))
                self.stdout.write("原因：这些有 AI 数据的项目可能不属于'江西/湖南/安徽/浙江'，被清洗脚本过滤掉了。")
                self.stdout.write("建议：你可以去数据库把某个 ID (如 15604) 的 region 改成 '江西'，然后重新运行 sync_bidding。")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 文件读取错误: {e}'))