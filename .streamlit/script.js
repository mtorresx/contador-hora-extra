document.addEventListener('DOMContentLoaded', function() {
    // Microinterações e animações refinadas

    // Smooth transitions e animações para cards
    const cards = document.querySelectorAll('.summary-card, .history-card, .stMetric');
    cards.forEach(card => {
        card.style.transition = 'all 0.3s ease';
    });

    // Melhorar formatação de inputs de hora
    const inputs = document.querySelectorAll('input[placeholder*="0"]');
    inputs.forEach(input => {
        if (input.placeholder.includes(':')) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');

                if (value.length > 4) {
                    value = value.substring(0, 4);
                }

                if (value.length >= 3) {
                    value = value.substring(0, 2) + ':' + value.substring(2);
                }

                e.target.value = value;
            });

            input.addEventListener('keydown', function(e) {
                if (e.key === ':') {
                    e.preventDefault();
                }
            });
        }
    });

    // Animação de sucesso nos alertas
    const alerts = document.querySelectorAll('[data-testid="stAlert"]');
    alerts.forEach(alert => {
        alert.style.animation = 'slideInUp 0.3s ease';
    });

    // Add event listeners para botões com efeito de ripple
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const ripple = document.createElement('span');
            ripple.style.position = 'absolute';
            ripple.style.borderRadius = '50%';
            ripple.style.pointerEvents = 'none';
            ripple.style.transition = 'all 0.6s ease';
            ripple.style.background = 'rgba(255, 255, 255, 0.5)';

            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.style.opacity = '0';
            ripple.style.transform = 'scale(0)';

            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);

            setTimeout(() => {
                ripple.style.transform = 'scale(2)';
                ripple.style.opacity = '0';
                setTimeout(() => ripple.remove(), 600);
            }, 0);
        });
    });
});