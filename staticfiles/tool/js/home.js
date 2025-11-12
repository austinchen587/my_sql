// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化粒子背景
    initParticleBackground();

    // 导航栏滚动效果
    window.addEventListener('scroll', handleNvBarScroll);

    // 特性卡片动画
    initFeatureCardsAnimation();
    
    // 按钮交互效果
    initButtonEffects();
});

// 粒子背景初始化
function initParticleBackground() {
    const bgContainer = document.getElementById('tech-bg');

    // 创建粒子
    for (let i = 0; i < 50; i++) {
        createParticle(bgContainer);
    }
}


// 创建单个粒子
function createParticle(container) {
    const particle = document.createElement('div');
    particle.classList.add('particle');
    
    // 随机属性
    const size = Math.random() * 3 + 1;
    const posX = Math.random() * 100;
    const posY = Math.random() * 100;
    const duration = Math.random() * 20 + 10;
    const delay = Math.random() * 5;
    
    // 设置样式
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    particle.style.left = `${posX}%`;
    particle.style.top = `${posY}%`;
    particle.style.animationDuration = `${duration}s`;
    particle.style.animationDelay = `${delay}s`;
    
    // 随机颜色
    const colors = ['#00ffff', '#0077ff', '#8a2be2'];
    const color = colors[Math.floor(Math.random() * colors.length)];
    particle.style.backgroundColor = color;
    particle.style.boxShadow = `0 0 10px ${color}`;
    
    container.appendChild(particle);
}

// 导航栏滚动效果

function handleNavbarScroll() {
    const navbar = document.querySelector('.glass-navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(10, 10, 30, 0.9)';
        navbar.style.padding = '10px 0';
    } else {
        navbar.style.background = 'rgba(10, 10, 30, 0.7)';
        navbar.style.padding = '15px 0';
    }
}

// 特性卡片动画

function initFeatureCardsAnimation() {
    const featureCards = document.querySelectorAll('.feature-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    featureCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

// 按钮交互效果
function initButtonEffects() {
    const ctaBtn = document.querySelector('.cta-btn');
    
    if (ctaBtn) {
        ctaBtn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px) scale(1.05)';
        });
        
        ctaBtn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    }

    // 为所有按钮添加点击波纹效果
    const buttons = document.querySelectorAll('.btn, .cta-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // 创建波纹元素
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            ripple.classList.add('ripple-effect');
            
            this.appendChild(ripple);
            
            // 移除波纹元素
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });


}


// 添加粒子动画的CSS（通过JS动态添加）
const particleStyles = `
    .particle {
        position: absolute;
        border-radius: 50%;
        opacity: 0.6;
        animation: floatParticle linear infinite;
    }
    
    @keyframes floatParticle {
        0% {
            transform: translateY(0) translateX(0);
            opacity: 0;
        }
        10% {
            opacity: 0.6;
        }
        90% {
            opacity: 0.6;
        }
        100% {
            transform: translateY(-100vh) translateX(20px);
            opacity: 0;
        }
    }
    
    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple 0.6s linear;
    }
    
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;

// 将样式添加到文档中

const styleSheet = document.createElement('style');
styleSheet.textContent = particleStyles;
document.head.appendChild(styleSheet);





