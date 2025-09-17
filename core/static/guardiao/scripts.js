/**
 * Sistema Guardião - JavaScript Principal - Atualizado - Versão Final - Estrutura Única - FORÇANDO CÓPIA
 * TIMESTAMP: 2025-09-17 22:31:30
 * FORÇANDO CÓPIA COM --clear
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
        this.lastCheck = null;
        this.currentSession = null;
        this.votingTimer = null;
        this.init();
    }

    init() {
        // Check for new reports every 5 seconds
        if (window.location.pathname.includes('/dashboard') || window.location.pathname === '/') {
            setInterval(this.checkForUpdates.bind(this), 5000);
            // Verificar se há denúncia pendente para o Guardião atual
            this.checkPendingReport();
        }
    }

    async checkForUpdates() {
        try {
            const url = this.lastCheck 
                ? `/api/reports/check-new/?last_check=${this.lastCheck}`
                : '/api/reports/check-new/';
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success && data.count > 0) {
                data.new_reports.forEach(report => {
                    this.showReportNotification(report);
                });
            }
            
            // Update last check timestamp
            this.lastCheck = data.timestamp;
        } catch (error) {
            console.error('Erro ao verificar atualizações:', error);
        }
    }

    showReportNotification(report) {
        // Play notification sound
        this.playNotificationSound();
        
        // Create popup notification
        const notification = document.createElement('div');
        notification.className = 'report-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-header">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Nova denúncia recebida!</span>
                </div>
                <div class="notification-body">
                    <p><strong>Reportado:</strong> ${this.formatDateTime(report.created_at)}</p>
                    <p><strong>Motivo:</strong> ${report.reason || 'Não especificado'}</p>
                </div>
                <div class="notification-actions">
                    <button class="btn btn-primary btn-sm attend-btn" data-report-id="${report.id}">
                        <i class="fas fa-hand-paper"></i> Atender
                    </button>
                    <button class="btn btn-secondary btn-sm dismiss-btn">
                        <i class="fas fa-times"></i> Dispensar
                    </button>
                </div>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto dismiss after 30 seconds
            setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 30000);
        
        // Add event listeners
        notification.querySelector('.attend-btn').addEventListener('click', () => {
            window.location.href = `/report/${report.id}/`;
        });
        
        notification.querySelector('.dismiss-btn').addEventListener('click', () => {
            notification.remove();
        });
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
    }

    playNotificationSound() {
        try {
            // Create audio context for notification sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create a simple beep sound
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            console.log('Não foi possível reproduzir o som de notificação:', error);
        }
    }

            formatDateTime(dateString) {
                const date = new Date(dateString);
                return date.toLocaleString('pt-BR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }

            async checkPendingReport() {
                try {
                    // Obter ID do Guardião atual (você precisará implementar isso)
                    const guardianId = this.getCurrentGuardianId();
                    if (!guardianId) return;

                    const response = await fetch(`/api/guardian/${guardianId}/pending-report/`);
                    const data = await response.json();

                    if (data.session_id && !this.currentSession) {
                        this.currentSession = data;
                        this.showVotingModal(data);
                    }
                } catch (error) {
                    console.error('Erro ao verificar denúncia pendente:', error);
                }
            }

            getCurrentGuardianId() {
                // Implementar lógica para obter ID do Guardião atual
                // Por enquanto, retornar null - você precisará implementar isso
                return null;
            }

            showVotingModal(sessionData) {
                // Criar modal de votação
                const modal = document.createElement('div');
                modal.className = 'voting-modal-overlay';
                modal.innerHTML = `
                    <div class="voting-modal">
                        <div class="modal-header">
                            <h2>Um caso de intimidação</h2>
                            <div class="timer" id="voting-timer">05:00</div>
                        </div>
                        
                        <div class="modal-content">
                            <div class="incident-section">
                                <h3>O INCIDENTE</h3>
                                <div class="chat-log" id="chat-log">
                                    ${this.renderChatMessages(sessionData.messages)}
                                </div>
                            </div>
                            
                            <div class="voting-section">
                                <h3>Como você acha que o usuário se comportou?</h3>
                                <div class="vote-buttons">
                                    <button class="vote-btn ok-btn" data-vote="improcedente">
                                        <i class="fas fa-smile"></i>
                                        <span>OK</span>
                                    </button>
                                    <button class="vote-btn intimidou-btn" data-vote="intimidou">
                                        <i class="fas fa-meh"></i>
                                        <span>Intimidou</span>
                                    </button>
                                    <button class="vote-btn grave-btn" data-vote="grave">
                                        <i class="fas fa-angry"></i>
                                        <span>GRAVE</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="modal-footer">
                            <button class="btn btn-secondary" id="leave-session">Sair da Sessão</button>
                        </div>
                    </div>
                `;

                document.body.appendChild(modal);
                this.startVotingTimer(sessionData.time_remaining);
                this.setupVotingEventListeners(sessionData);
            }

            renderChatMessages(messages) {
                return messages.map(msg => `
                    <div class="message ${msg.is_reported_user ? 'reported-user' : ''}">
                        <div class="message-header">
                            <span class="username">${msg.anonymized_username}</span>
                            <span class="timestamp">${this.formatDateTime(msg.timestamp)}</span>
                        </div>
                        <div class="message-content">${msg.content}</div>
                    </div>
                `).join('');
            }

            startVotingTimer(timeRemaining) {
                let timeLeft = timeRemaining || 300; // 5 minutos padrão
                
                this.votingTimer = setInterval(() => {
                    const minutes = Math.floor(timeLeft / 60);
                    const seconds = timeLeft % 60;
                    
                    const timerElement = document.getElementById('voting-timer');
                    if (timerElement) {
                        timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                    }
                    
                    timeLeft--;
                    
                    if (timeLeft < 0) {
                        this.expireVotingSession();
                    }
                }, 1000);
            }

            setupVotingEventListeners(sessionData) {
                // Event listeners para botões de voto
                document.querySelectorAll('.vote-btn').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        const voteType = e.currentTarget.dataset.vote;
                        await this.castVote(sessionData.session_id, voteType);
                    });
                });

                // Event listener para sair da sessão
                document.getElementById('leave-session').addEventListener('click', async () => {
                    await this.leaveVotingSession(sessionData.session_id);
                });
            }

            async castVote(sessionId, voteType) {
                try {
                    const guardianId = this.getCurrentGuardianId();
                    const response = await fetch('/api/session/vote/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCSRFToken()
                        },
                        body: JSON.stringify({
                            session_id: sessionId,
                            guardian_id: guardianId,
                            vote_type: voteType
                        })
                    });

                    const data = await response.json();

                    if (data.success) {
                        this.showVoteConfirmation(data);
                        if (data.session_completed) {
                            this.showFinalDecision(sessionId);
                        }
                    } else {
                        alert('Erro ao registrar voto: ' + data.error);
                    }
                } catch (error) {
                    console.error('Erro ao votar:', error);
                    alert('Erro ao registrar voto');
                }
            }

            showVoteConfirmation(voteData) {
                // Desabilitar botões de voto
                document.querySelectorAll('.vote-btn').forEach(btn => {
                    btn.disabled = true;
                    btn.classList.add('disabled');
                });

                // Mostrar confirmação
                const confirmation = document.createElement('div');
                confirmation.className = 'vote-confirmation';
                confirmation.innerHTML = `
                    <div class="confirmation-content">
                        <i class="fas fa-check-circle"></i>
                        <span>Voto registrado com sucesso!</span>
                        <p>Aguardando outros Guardiões votarem... (${voteData.votes_count}/5)</p>
                    </div>
                `;

                document.querySelector('.voting-section').appendChild(confirmation);
            }

            async showFinalDecision(sessionId) {
                // Implementar lógica para mostrar decisão final
                // Por enquanto, apenas fechar o modal
                this.closeVotingModal();
            }

            async leaveVotingSession(sessionId) {
                try {
                    const guardianId = this.getCurrentGuardianId();
                    const response = await fetch('/api/session/leave/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCSRFToken()
                        },
                        body: JSON.stringify({
                            session_id: sessionId,
                            guardian_id: guardianId
                        })
                    });

                    const data = await response.json();
                    if (data.success) {
                        this.closeVotingModal();
                    }
                } catch (error) {
                    console.error('Erro ao sair da sessão:', error);
                }
            }

            expireVotingSession() {
                if (this.votingTimer) {
                    clearInterval(this.votingTimer);
                }
                
                alert('Tempo de votação expirado!');
                this.closeVotingModal();
            }

            closeVotingModal() {
                const modal = document.querySelector('.voting-modal-overlay');
                if (modal) {
                    modal.remove();
                }
                
                if (this.votingTimer) {
                    clearInterval(this.votingTimer);
                }
                
                this.currentSession = null;
            }

            getCSRFToken() {
                return document.querySelector('[name=csrfmiddlewaretoken]').value;
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
