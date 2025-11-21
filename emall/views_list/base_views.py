from django.views.generic import TemplateView

class ProcurementListView(TemplateView):
    """采购列表页面视图"""
    template_name = 'emall/procurement_list.html'
