/**
 * Sistema Guardião - JavaScript Principal - Atualizado - Versão Final - Estrutura Única
 */

// Utilitários
const Utils = {
    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Format date
    formatDate(date) {
        return new Date(date).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            ${message}
        `;
        
        const messagesContainer = document.querySelector('.messages .container') || document.querySelector('.main');
        if (messagesContainer) {
            messagesContainer.insertBefore(notification, messagesContainer.firstChild);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }
    },

    // AJAX helper
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
        };

        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Erro na requisição');
            }
            
            return data;
        } catch (error) {
            console.error('Erro na requisição:', error);
            throw error;
        }
    }
};

// Status Toggle
class StatusToggle {
    constructor() {
        this.init();
    }

    init() {
        const toggleButton = document.querySelector('.btn-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', this.toggleStatus.bind(this));
        }
    }

    async toggleStatus() {
        const currentStatus = document.querySelector('.status-indicator').classList.contains('online') ? 'online' : 'offline';
        const newStatus = currentStatus === 'online' ? 'offline' : 'online';

        try {
            const data = await Utils.request('/api/status/', {
                method: 'POST',
                body: JSON.stringify({ status: newStatus })
            });

            if (data.success) {
                Utils.showNotification(`Status alterado para: ${data.status_display}`, 'success');
                setTimeout(() => location.reload(), 1000);
            }
        } catch (error) {
            Utils.showNotification(`Erro ao alterar status: ${error.message}`, 'error');
        }
    }
}

// Vote System
class VoteSystem {
    constructor() {
        this.init();
    }

    init() {
        const voteForm = document.getElementById('voteForm');
        if (voteForm) {
            voteForm.addEventListener('submit', this.handleVote.bind(this));
        }
    }

    async handleVote(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const voteType = formData.get('vote_type');
        
        if (!voteType) {
            Utils.showNotification('Por favor, selecione uma opção de voto.', 'error');
            return;
        }

        // Confirm vote
        const voteLabels = {
            'improcedente': 'Improcedente',
            'intimidou': 'Intimidou',
            'grave': 'Grave'
        };

        if (!confirm(`Tem certeza de que deseja votar "${voteLabels[voteType]}"? Esta ação não pode ser desfeita.`)) {
            return;
        }

        const reportId = window.location.pathname.match(/\/report\/(\d+)\//)?.[1];
        if (!reportId) {
            Utils.showNotification('Erro: ID da denúncia não encontrado.', 'error');
            return;
        }

        try {
            const data = await Utils.request(`/api/vote/${reportId}/`, {
                method: 'POST',
                body: JSON.stringify({ vote_type: voteType })
            });

            if (data.success) {
                Utils.showNotification('Voto registrado com sucesso!', 'success');
                setTimeout(() => location.reload(), 1000);
            }
        } catch (error) {
            Utils.showNotification(`Erro ao registrar voto: ${error.message}`, 'error');
        }
    }
}

// Real-time Updates
class RealTimeUpdates {
    constructor() {
        this.init();
    }

    init() {
        // Check for new reports every 30 seconds
        if (window.location.pathname.includes('/dashboard')) {
            setInterval(this.checkForUpdates.bind(this), 30000);
        }
    }

    async checkForUpdates() {
        try {
            const response = await fetch('/api/dashboard/updates/');
            const data = await response.json();
            
            if (data.new_reports > 0) {
                this.showNewReportsNotification(data.new_reports);
            }
        } catch (error) {
            console.error('Erro ao verificar atualizações:', error);
        }
    }

    showNewReportsNotification(count) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info';
        notification.innerHTML = `
            <i class="fas fa-bell"></i>
            ${count} nova(s) denúncia(s) disponível(is) para análise!
            <a href="/reports/" class="btn btn-sm btn-primary ml-2">Ver Denúncias</a>
        `;
        
        const messagesContainer = document.querySelector('.messages .container');
        if (messagesContainer) {
            messagesContainer.insertBefore(notification, messagesContainer.firstChild);
            
            // Auto remove after 10 seconds
            setTimeout(() => {
                notification.remove();
            }, 10000);
        }
    }
}

// Theme System
class ThemeSystem {
    constructor() {
        this.init();
    }

    init() {
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.setTheme(savedTheme);
        
        // Add theme toggle button if not exists
        this.addThemeToggle();
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }

    addThemeToggle() {
        const nav = document.querySelector('.nav');
        if (nav && !document.querySelector('.theme-toggle')) {
            const themeToggle = document.createElement('button');
            themeToggle.className = 'nav-link theme-toggle';
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            themeToggle.title = 'Alternar tema';
            
            themeToggle.addEventListener('click', () => {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                this.setTheme(newTheme);
                
                const icon = themeToggle.querySelector('i');
                icon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
            });
            
            nav.appendChild(themeToggle);
        }
    }
}

// Loading States
class LoadingStates {
    constructor() {
        this.init();
    }

    init() {
        // Add loading states to forms
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Add loading states to buttons
        document.addEventListener('click', this.handleButtonClick.bind(this));
    }

    handleFormSubmit(event) {
        const form = event.target;
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton) {
            this.setButtonLoading(submitButton, true);
            
            // Reset after 10 seconds (fallback)
            setTimeout(() => {
                this.setButtonLoading(submitButton, false);
            }, 10000);
        }
    }

    handleButtonClick(event) {
        const button = event.target.closest('.btn');
        if (button && button.classList.contains('btn-primary')) {
            this.setButtonLoading(button, true);
            
            // Reset after 5 seconds (fallback)
            setTimeout(() => {
                this.setButtonLoading(button, false);
            }, 5000);
        }
    }

    setButtonLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Carregando...';
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalText || button.innerHTML;
        }
    }
}

// Keyboard Shortcuts
class KeyboardShortcuts {
    constructor() {
        this.init();
    }

    init() {
        document.addEventListener('keydown', this.handleKeydown.bind(this));
    }

    handleKeydown(event) {
        // Ctrl/Cmd + K - Focus search
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape - Close modals/alerts
        if (event.key === 'Escape') {
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => alert.remove());
        }
    }
}

// Smooth Scrolling
class SmoothScrolling {
    constructor() {
        this.init();
    }

    init() {
        // Add smooth scrolling to anchor links
        document.addEventListener('click', (event) => {
            const link = event.target.closest('a[href^="#"]');
            if (link) {
                event.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new StatusToggle();
    new VoteSystem();
    new RealTimeUpdates();
    new ThemeSystem();
    new LoadingStates();
    new KeyboardShortcuts();
    new SmoothScrolling();
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.stat-card, .feature-card, .report-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// Export for global access
window.GuardiaoUtils = Utils;
