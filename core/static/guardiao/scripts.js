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
            console.log('🔄 Alterando status para:', newStatus);
            const data = await Utils.request('/api/guardians/status/', {
                method: 'POST',
                body: JSON.stringify({ status: newStatus })
            });

            console.log('📊 Resposta da API:', data);
            if (data.success) {
                Utils.showNotification(`Status alterado para: ${data.status_display}`, 'success');
                setTimeout(() => location.reload(), 1000);
            }
        } catch (error) {
            console.error('❌ Erro ao alterar status:', error);
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
                this.lastNotificationTime = 0; // Para cooldown de notificação
        this.clearOldLocalStorage();
        this.init();
    }
    
    // Limpar localStorage antigo ao inicializar
    clearOldLocalStorage() {
        console.log('🧹 Limpando localStorage antigo...');
        localStorage.removeItem('guardian_discord_id');
        console.log('✅ localStorage limpo');
    }

            init() {
                // Check for new reports every 5 seconds
                if (window.location.pathname.includes('/dashboard') || window.location.pathname === '/') {
                    setInterval(this.checkForUpdates.bind(this), 5000);
                    // Verificar se há denúncia pendente para o Guardião atual
                    this.checkPendingReport();
                    // Verificar denúncias pendentes a cada 1 minuto (60000ms)
                    setInterval(this.checkPendingReport.bind(this), 60000);
                } else {
                    // Se não estiver no dashboard, fechar qualquer modal/notificação aberta
                    this.closeVotingModal();
                    this.dismissNotification();
                }
            }

    async checkForUpdates() {
        try {
            const url = this.lastCheck 
                ? `/api/reports/check-new/?last_check=${this.lastCheck}`
                : '/api/reports/check-new/';

            const response = await fetch(url);
            const data = await response.json();
            
            // Sistema antigo de notificações desabilitado
            // Agora usamos apenas o modal de votação
            console.log('📊 Verificação de atualizações:', data.count, 'novas denúncias');

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
            // Usar o sistema de fila em vez do link antigo
            this.checkPendingReport();
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
                    // Verificar se o usuário está logado (verificar se há sessão ativa)
                    const sessionCheck = await fetch('/api/auth/check-session/', {
                        method: 'GET',
                        credentials: 'include'
                    });
                    
                    if (!sessionCheck.ok) {
                        console.log('🚪 Usuário não logado - não verificando denúncias pendentes');
                        this.closeVotingModal();
                        this.dismissNotification();
                        return;
                    }
                    
                    const sessionData = await sessionCheck.json();
                    if (!sessionData.authenticated) {
                        console.log('🚪 Sessão inválida - não verificando denúncias pendentes');
                        this.closeVotingModal();
                        this.dismissNotification();
                        return;
                    }

                    // Obter ID do Guardião atual
                    const guardianId = await this.getCurrentGuardianId();
                    console.log('🔍 Verificando denúncia pendente para Guardião ID:', guardianId);
                    
                    if (!guardianId) {
                        console.warn('⚠️ ID do Guardião não encontrado');
                        return;
                    }

                    // Primeiro verificar se o Guardião está online
                    const statusResponse = await fetch(`/api/guardian/${guardianId}/status/`);
                    const statusData = await statusResponse.json();
                    
                    console.log('👤 Status do Guardião:', statusData);

                    if (!statusData.success) {
                        console.warn('❌ Guardião não encontrado:', statusData.error);
                        return;
                    }

                    if (!statusData.is_online) {
                        console.log('⏸️ Guardião offline - não verificando denúncias pendentes');
                        // Fechar modal se estiver aberto
                        this.closeVotingModal();
                        // Fechar notificação se estiver aberta
                        this.dismissNotification();
                        return;
                    }

                    console.log('✅ Guardião online - verificando denúncias pendentes');

                    const response = await fetch(`/api/guardian/${guardianId}/pending-report/`);
                    const data = await response.json();
                    
                    console.log('📋 Resposta da API:', data);

                    if (data.session_id && !this.currentSession) {
                        console.log('🎯 Nova sessão encontrada:', data.session_id);
                        this.currentSession = data;
                        this.showNotificationPopup(data);
                    } else if (data.message) {
                        console.log('ℹ️', data.message);
                    } else if (data.error) {
                        console.log('⚠️ Erro:', data.error);
                    }
                } catch (error) {
                    console.error('❌ Erro ao verificar denúncia pendente:', error);
                }
            }

            async getCurrentGuardianId() {
                // Tentar obter ID do Guardião de diferentes formas
                console.log('🔍 Buscando ID do Guardião...');
                console.log('🔍 window.GUARDIAN_DISCORD_ID:', window.GUARDIAN_DISCORD_ID);
                console.log('🔍 localStorage guardian_discord_id:', localStorage.getItem('guardian_discord_id'));
                
                // 1. Verificar variável global (desabilitado - pode estar incorreta)
                if (window.GUARDIAN_DISCORD_ID) {
                    console.log('⚠️ Variável global encontrada mas ignorada:', window.GUARDIAN_DISCORD_ID);
                    console.log('🔄 Usando sessão atual em vez da variável global');
                }
                
                // 2. Obter ID da sessão atual (mais confiável que localStorage)
                try {
                    const sessionResponse = await fetch('/api/auth/check-session/', {
                        method: 'GET',
                        credentials: 'include'
                    });
                    
           if (sessionResponse.ok) {
               const responseText = await sessionResponse.text();
               console.log('🔍 Resposta bruta da API:', responseText);
               const sessionData = JSON.parse(responseText);
               console.log('🔍 Dados da sessão recebidos:', sessionData);
               console.log('🔍 sessionData.authenticated:', sessionData.authenticated);
               console.log('🔍 sessionData.guardian_id:', sessionData.guardian_id);
               console.log('🔍 Tipo do guardian_id:', typeof sessionData.guardian_id);
               
               // CORREÇÃO: Manter guardian_id como string para evitar perda de precisão
               if (sessionData.guardian_id) {
                   sessionData.guardian_id = String(sessionData.guardian_id);
                   console.log('🔧 guardian_id convertido para string:', sessionData.guardian_id);
               }
                        
                        if (sessionData.authenticated && sessionData.guardian_id) {
                            console.log('✅ ID encontrado na sessão atual:', sessionData.guardian_id);
                            // Limpar localStorage antigo e definir o correto
                            localStorage.removeItem('guardian_discord_id');
                            localStorage.setItem('guardian_discord_id', sessionData.guardian_id);
                            // CORREÇÃO: Retornar como string para evitar perda de precisão
                            return sessionData.guardian_id;
                        } else {
                            console.log('❌ Sessão inválida ou guardian_id ausente');
                        }
                    } else {
                        console.log('❌ Resposta da sessão não OK:', sessionResponse.status);
                    }
                } catch (error) {
                    console.warn('⚠️ Erro ao verificar sessão:', error);
                }
                
       // 3. Verificar se está armazenado no localStorage (fallback)
       let guardianId = localStorage.getItem('guardian_discord_id');
       if (guardianId) {
           console.log('✅ ID encontrado no localStorage:', guardianId);
           return guardianId; // CORREÇÃO: Retornar como string
       }
                
                // 3. Verificar se está em um elemento hidden na página
                const hiddenInput = document.querySelector('input[name="guardian_discord_id"]');
                if (hiddenInput && hiddenInput.value) {
                    console.log('✅ ID encontrado no input hidden:', hiddenInput.value);
                    localStorage.setItem('guardian_discord_id', hiddenInput.value);
                    return hiddenInput.value; // CORREÇÃO: Retornar como string
                }
                
                // 4. Verificar se está em um data attribute do body
                const bodyGuardianId = document.body.dataset.guardianId;
                if (bodyGuardianId) {
                    console.log('✅ ID encontrado no data attribute do body:', bodyGuardianId);
                    localStorage.setItem('guardian_discord_id', bodyGuardianId);
                    return bodyGuardianId; // CORREÇÃO: Retornar como string
                }
                
                // 5. Tentar obter da URL ou parâmetros
                const urlParams = new URLSearchParams(window.location.search);
                const urlGuardianId = urlParams.get('guardian_id');
                if (urlGuardianId) {
                    console.log('✅ ID encontrado na URL:', urlGuardianId);
                    localStorage.setItem('guardian_discord_id', urlGuardianId);
                    return urlGuardianId; // CORREÇÃO: Retornar como string
                }
                
                console.warn('❌ ID do Guardião não encontrado em nenhum local. Modal não será exibido.');
                console.log('🔍 Elementos verificados:');
                console.log('  - window.GUARDIAN_DISCORD_ID:', window.GUARDIAN_DISCORD_ID);
                console.log('  - localStorage:', localStorage.getItem('guardian_discord_id'));
                console.log('  - input hidden:', document.querySelector('input[name="guardian_discord_id"]'));
                console.log('  - body data attribute:', document.body.dataset.guardianId);
                console.log('  - URL params:', new URLSearchParams(window.location.search).get('guardian_id'));
                return null;
            }

            showNotificationPopup(sessionData) {
                // Verificar cooldown (1 minuto = 60000ms)
                const now = Date.now();
                if (now - this.lastNotificationTime < 60000) {
                    console.log('⏳ Notificação em cooldown, pulando...');
                    return;
                }
                this.lastNotificationTime = now;
                
                // Verificar se já existe uma notificação aberta
                const existingNotification = document.querySelector('.notification-popup-corner');
                if (existingNotification) {
                    console.log('⏳ Notificação já existe, pulando...');
                    return;
                }

                // Criar pop-up de notificação no canto superior direito
                const notification = document.createElement('div');
                notification.className = 'notification-popup-corner';
                notification.innerHTML = `
                    <div class="notification-popup">
                        <div class="notification-header">
                            <i class="fas fa-exclamation-triangle"></i>
                            <h3>Nova Denúncia Recebida!</h3>
                        </div>
                        <div class="notification-content">
                            <p>Uma nova denúncia está aguardando sua análise.</p>
                            <div class="notification-details">
                                <span class="report-id">Denúncia #${sessionData.report_id}</span>
                                <span class="reason">${sessionData.report.reason}</span>
                            </div>
                        </div>
                        <div class="notification-actions">
                            <button class="btn btn-secondary" id="dismiss-notification">
                                <i class="fas fa-times"></i>
                                Dispensar
                            </button>
                            <button class="btn btn-primary" id="enter-session">
                                <i class="fas fa-play"></i>
                                Entrar
                            </button>
                        </div>
                    </div>
                `;

                document.body.appendChild(notification);
                
                // Event listeners
                document.getElementById('dismiss-notification').addEventListener('click', () => {
                    this.dismissNotification();
                });
                
                document.getElementById('enter-session').addEventListener('click', () => {
                    this.enterVotingSession(sessionData);
                });
                
                // Tocar som de notificação
                this.playNotificationSound();
            }

            dismissNotification() {
                const notification = document.querySelector('.notification-popup-corner');
                if (notification) {
                    notification.remove();
                }
                this.currentSession = null;
            }

            enterVotingSession(sessionData) {
                // Remover pop-up de notificação
                const notification = document.querySelector('.notification-popup-corner');
                if (notification) {
                    notification.remove();
                }
                
                // Mostrar modal de votação
                this.showVotingModal(sessionData);
            }

            showVotingModal(sessionData) {
                // Criar modal de votação igual à imagem
                const modal = document.createElement('div');
                modal.className = 'voting-modal-overlay';
                modal.innerHTML = `
                    <div class="voting-modal-new">
                        <!-- Token CSRF para o modal -->
                        <input type="hidden" name="csrfmiddlewaretoken" value="${this.getCSRFToken()}">
                        
                        <div class="modal-header-new">
                            <h2>Um caso de intimidação</h2>
                            <div class="timer-new" id="voting-timer">05:00</div>
                        </div>
                        
                        <div class="modal-content-new">
                            <div class="left-panel">
                                <div class="incident-section-new">
                                    <h3>O INCIDENTE</h3>
                                    <div class="chat-log-new" id="chat-log">
                                        ${this.renderChatMessages(sessionData.messages)}
                                    </div>
                                </div>
                                
                                <div class="voting-section-new">
                                    <h3>Como você acha que o usuário se comportou?</h3>
                                    <div class="vote-buttons-new">
                                        <button class="vote-btn-new ok-btn-new" data-vote="improcedente">
                                            <div class="vote-icon">😇</div>
                                            <span>OK</span>
                                        </button>
                                        <button class="vote-btn-new intimidou-btn-new" data-vote="intimidou">
                                            <div class="vote-icon">😐</div>
                                            <span>Intimidou</span>
                                        </button>
                                        <button class="vote-btn-new grave-btn-new" data-vote="grave">
                                            <div class="vote-icon">😈</div>
                                            <span>GRAVE</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="right-panel">
                                <div class="guardians-section">
                                    <h3>GUARDIÕES</h3>
                                    <div class="guardians-list" id="guardians-list">
                                        ${this.renderGuardiansList(sessionData)}
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="modal-footer-new">
                            <button class="btn btn-secondary" id="leave-session">Sair da Sessão</button>
                        </div>
                    </div>
                `;

                document.body.appendChild(modal);
                this.startVotingTimer(sessionData.time_remaining);
                this.setupVotingEventListeners(sessionData);
            }

            renderChatMessages(messages) {
                return messages.map(msg => {
                    let attachmentsHtml = '';
                    
                    // Renderizar anexos se existirem
                    if (msg.has_attachments && msg.attachments_info) {
                        attachmentsHtml = msg.attachments_info.map(attachment => {
                            if (attachment.is_image) {
                                return `<div class="attachment-image"><img src="${attachment.url}" alt="${attachment.filename}" style="max-width: 300px; max-height: 200px; border-radius: 8px; margin-top: 8px;"></div>`;
                            } else if (attachment.is_video) {
                                return `<div class="attachment-video"><video src="${attachment.url}" controls style="max-width: 300px; max-height: 200px; border-radius: 8px; margin-top: 8px;"></video></div>`;
                            } else if (attachment.type === 'custom_emoji') {
                                return `<div class="attachment-emoji"><img src="${attachment.url}" alt="${attachment.name}" style="width: 32px; height: 32px; margin-top: 4px;"></div>`;
                            } else if (attachment.type === 'sticker') {
                                return `<div class="attachment-sticker"><img src="${attachment.url}" alt="${attachment.name}" style="width: 64px; height: 64px; margin-top: 4px;"></div>`;
                            } else {
                                return `<div class="attachment-file"><a href="${attachment.url}" target="_blank" style="color: #58A6FF; text-decoration: none;">📎 ${attachment.filename}</a></div>`;
                            }
                        }).join('');
                    }
                    
                    return `
                        <div class="message-new ${msg.is_reported_user ? 'reported-user-new' : ''}">
                            <div class="message-header-new">
                                <span class="username-new">${msg.anonymized_username}</span>
                                <span class="timestamp-new">${this.formatDateTime(msg.timestamp)}</span>
                            </div>
                            <div class="message-content-new">${msg.content}</div>
                            ${attachmentsHtml}
                        </div>
                    `;
                }).join('');
            }

            renderGuardiansList(sessionData) {
                // Mostrar 5 slots para Guardiões numerados de 1 a 5
                const guardians = [
                    { id: 1, name: 'Guardião 1', status: 'waiting', vote: null },
                    { id: 2, name: 'Guardião 2', status: 'waiting', vote: null },
                    { id: 3, name: 'Guardião 3', status: 'waiting', vote: null },
                    { id: 4, name: 'Guardião 4', status: 'waiting', vote: null },
                    { id: 5, name: 'Guardião 5', status: 'current', vote: null }
                ];
                
                return guardians.map(guardian => `
                    <div class="guardian-item ${guardian.status === 'current' ? 'current-guardian' : ''}" data-guardian-id="${guardian.id}">
                        <div class="guardian-avatar" id="avatar-${guardian.id}">
                            ${guardian.status === 'current' ? '👤' : '<div class="loading-spinner-small"></div>'}
                        </div>
                        <div class="guardian-info">
                            <span class="guardian-name">${guardian.name}</span>
                            <div class="guardian-status">
                                ${this.getGuardianStatusText(guardian.status)}
                            </div>
                        </div>
                        <div class="guardian-vote" id="vote-${guardian.id}">
                            ${this.getVoteIcon(guardian.vote)}
                        </div>
                    </div>
                `).join('');
            }

            getGuardianStatusText(status) {
                switch(status) {
                    case 'waiting': return 'Aguardando...';
                    case 'current': return 'Sua vez!';
                    case 'voted': return 'Votou';
                    default: return 'Aguardando...';
                }
            }

            getVoteIcon(vote) {
                switch(vote) {
                    case 'improcedente': return '😇';
                    case 'intimidou': return '😐';
                    case 'grave': return '😈';
                    default: return '';
                }
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
                document.querySelectorAll('.vote-btn-new').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        const voteType = e.currentTarget.dataset.vote;
                        console.log('🗳️ Voto clicado:', voteType);
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
                    const guardianId = await this.getCurrentGuardianId();
                    console.log('🔍 guardianId obtido para voto:', guardianId);
                    console.log('🔍 Tipo do guardianId:', typeof guardianId);
                    
                    if (!guardianId) {
                        alert('Erro: ID do Guardião não encontrado. Faça login novamente.');
                        return;
                    }
                    
                    console.log('🚀 Enviando voto para API:', {
                        session_id: sessionId,
                        guardian_id: guardianId,
                        vote_type: voteType
                    });

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

                    console.log('📡 Resposta da API recebida:', response.status, response.statusText);
                    const data = await response.json();
                    console.log('📋 Dados da resposta:', data);

                    if (data.success) {
                        // Adicionar vote_type à resposta da API
                        data.vote_type = voteType;
                        this.showVoteConfirmation(data);
                        this.updateAnonymousVotes(data.anonymous_votes);
                        this.updateGuardiansSection(data.guardians_info);
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
                console.log('🎯 showVoteConfirmation chamada com:', voteData);
                
                // Desabilitar botões de voto
                document.querySelectorAll('.vote-btn-new').forEach(btn => {
                    btn.disabled = true;
                    btn.classList.add('disabled');
                    btn.classList.remove('voted'); // Remover classe voted de todos
                });

                // Destacar o botão que foi votado
                console.log('🔍 Procurando botão com data-vote:', voteData.vote_type);
                const votedButton = document.querySelector(`.vote-btn-new[data-vote="${voteData.vote_type}"]`);
                console.log('🔍 Botão votado encontrado:', votedButton);
                
                if (votedButton) {
                    votedButton.classList.remove('disabled'); // Remover disabled do botão votado
                    votedButton.disabled = false; // Reabilitar para que os estilos funcionem
                    votedButton.classList.add('voted');
                    console.log('✅ Classe voted adicionada ao botão:', votedButton.className);
                    console.log('✅ Estilos aplicados:', votedButton.style.cssText);
                    
                    // Atualizar slot "Você" na seção de guardiões
                    this.updateCurrentUserSlot(voteData.vote_type);
                } else {
                    console.error('❌ Botão votado não encontrado para:', voteData.vote_type);
                    // Tentar encontrar todos os botões para debug
                    const allButtons = document.querySelectorAll('.vote-btn-new');
                    console.log('🔍 Todos os botões encontrados:', allButtons);
                    allButtons.forEach((btn, index) => {
                        console.log(`Botão ${index}:`, btn.dataset.vote, btn);
                    });
                }
            }

            updateAnonymousVotes(anonymousVotes) {
                console.log('🔍 Atualizando votos anônimos:', anonymousVotes);
                
                // Buscar ou criar seção de votos anônimos
                let votesSection = document.querySelector('.anonymous-votes-section');
                if (!votesSection) {
                    votesSection = document.createElement('div');
                    votesSection.className = 'anonymous-votes-section';
                    votesSection.innerHTML = `
                        <h4>📊 Votos Registrados</h4>
                        <div class="votes-list"></div>
                    `;
                    
                    const modalContent = document.querySelector('.voting-modal-content');
                    if (modalContent) {
                        modalContent.appendChild(votesSection);
                    }
                }
                
                // Atualizar lista de votos
                const votesList = votesSection.querySelector('.votes-list');
                votesList.innerHTML = '';
                
                anonymousVotes.forEach((vote, index) => {
                    const voteElement = document.createElement('div');
                    voteElement.className = 'vote-item';
                    voteElement.innerHTML = `
                        <span class="vote-number">${index + 1}</span>
                        <span class="vote-type ${vote.vote_type}">${vote.vote_display}</span>
                        <span class="vote-time">${new Date(vote.timestamp).toLocaleTimeString()}</span>
                    `;
                    votesList.appendChild(voteElement);
                });
            }

            updateCurrentUserSlot(voteType) {
                console.log('🎯 Atualizando slot do usuário atual com voto:', voteType);
                
                // Buscar o slot do usuário atual (guardian-id="5")
                const currentUserSlot = document.querySelector('.guardian-item[data-guardian-id="5"]');
                if (!currentUserSlot) {
                    console.log('❌ Slot do usuário atual não encontrado');
                    return;
                }
                
                const nameElement = currentUserSlot.querySelector('.guardian-name');
                const statusElement = currentUserSlot.querySelector('.guardian-status');
                const voteElement = currentUserSlot.querySelector('.guardian-vote');
                
                if (nameElement) {
                    nameElement.textContent = 'Você';
                }
                
                if (statusElement) {
                    statusElement.textContent = 'Votou';
                }
                
                if (voteElement) {
                    voteElement.innerHTML = this.getVoteIcon(voteType);
                }
            }

            updateGuardiansSection(guardiansInfo) {
                console.log('🔍 Atualizando seção de guardiões:', guardiansInfo);
                
                // Buscar lista de guardiões
                const guardiansList = document.querySelector('.guardians-list');
                if (!guardiansList) {
                    console.log('❌ Lista de guardiões não encontrada');
                    return;
                }
                
                // Manter o visual original com 5 slots fixos
                const guardianItems = guardiansList.querySelectorAll('.guardian-item');
                
                // Contar votos para distribuir nos slots
                const votedGuardians = guardiansInfo.filter(g => g.has_voted);
                const waitingGuardians = guardiansInfo.filter(g => !g.has_voted && g.is_active);
                
                // Atualizar cada slot
                guardianItems.forEach((item, index) => {
                    const guardianId = item.dataset.guardianId;
                    const avatarElement = item.querySelector('.guardian-avatar');
                    const statusElement = item.querySelector('.guardian-status');
                    const voteElement = item.querySelector('.guardian-vote');
                    const nameElement = item.querySelector('.guardian-name');
                    
                    if (guardianId === '5') {
                        // Slot do usuário atual - mostrar "Você" e status atual
                        if (nameElement) {
                            nameElement.textContent = 'Você';
                        }
                        if (statusElement) {
                            statusElement.textContent = 'Sua vez!';
                        }
                        if (avatarElement) {
                            avatarElement.innerHTML = '👤';
                        }
                    } else {
                        // Slots dos outros guardiões
                        if (index < votedGuardians.length) {
                            // Mostrar voto anônimo
                            const votedGuardian = votedGuardians[index];
                            if (statusElement) {
                                statusElement.textContent = 'Votou';
                            }
                            if (voteElement) {
                                voteElement.innerHTML = this.getVoteIcon(votedGuardian.vote_type);
                            }
                            if (avatarElement) {
                                avatarElement.innerHTML = '👤';
                            }
                        } else {
                            // Mostrar aguardando
                            if (statusElement) {
                                statusElement.textContent = 'Aguardando...';
                            }
                            if (voteElement) {
                                voteElement.innerHTML = '';
                            }
                            if (avatarElement) {
                                avatarElement.innerHTML = '<div class="loading-spinner-small"></div>';
                            }
                        }
                    }
                });
            }

            async showFinalDecision(sessionId) {
                // Implementar lógica para mostrar decisão final
                // Por enquanto, apenas fechar o modal
                this.closeVotingModal();
            }

            async leaveVotingSession(sessionId) {
                try {
                    const guardianId = await this.getCurrentGuardianId();
                    console.log('🔍 guardianId obtido para sair da sessão:', guardianId);
                    console.log('🔍 Tipo do guardianId:', typeof guardianId);
                    
                    if (!guardianId) {
                        alert('Erro: ID do Guardião não encontrado. Faça login novamente.');
                        return;
                    }
                    
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
                    console.log('🔍 Resposta da API leave:', data);
                    
                    if (data.success) {
                        this.closeVotingModal();
                    } else {
                        alert('Erro ao sair da sessão: ' + (data.error || 'Erro desconhecido'));
                    }
                } catch (error) {
                    console.error('Erro ao sair da sessão:', error);
                    alert('Erro ao sair da sessão: ' + error.message);
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
                
                // Também remover pop-up de notificação se existir
                const notification = document.querySelector('.notification-popup-corner');
                if (notification) {
                    notification.remove();
                }
                
                if (this.votingTimer) {
                    clearInterval(this.votingTimer);
                }
                
                this.currentSession = null;
            }

            getCSRFToken() {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfToken) {
                    return csrfToken.value;
                }
                
                // Tentar obter do cookie se não encontrar no DOM
                const cookies = document.cookie.split(';');
                for (let cookie of cookies) {
                    const [name, value] = cookie.trim().split('=');
                    if (name === 'csrftoken') {
                        return value;
                    }
                }
                
                console.warn('⚠️ Token CSRF não encontrado');
                return '';
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
