class FlowChat {
    constructor() {
        this.messages = document.getElementById('messages');
        this.input = document.getElementById('input');
        this.sendBtn = document.getElementById('send');
        this.isTyping = false;
        this.messageDelay = 0;
        
        this.init();
    }
    
    init() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.input.addEventListener('input', () => {
            this.autoResize();
            this.updateSendButton();
        });
        
        // Focus input on load
        setTimeout(() => this.input.focus(), 100);
        
        this.updateSendButton();
        this.animateInitialMessage();
    }
    
    animateInitialMessage() {
        const initialMsg = this.messages.querySelector('.message');
        if (initialMsg) {
            setTimeout(() => {
                initialMsg.style.animationDelay = '0.5s';
            }, 100);
        }
    }
    
    autoResize() {
        this.input.style.height = 'auto';
        const newHeight = Math.min(this.input.scrollHeight, 120);
        this.input.style.height = newHeight + 'px';
    }
    
    updateSendButton() {
        const hasText = this.input.value.trim().length > 0;
        this.sendBtn.disabled = !hasText || this.isTyping;
        
        if (hasText && !this.isTyping) {
            this.sendBtn.style.transform = 'scale(1)';
            this.sendBtn.style.opacity = '1';
        } else {
            this.sendBtn.style.transform = 'scale(0.8)';
            this.sendBtn.style.opacity = '0.4';
        }
    }
    
    async sendMessage() {
        const text = this.input.value.trim();
        if (!text || this.isTyping) return;
        
        // Add haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(10);
        }
        
        this.addMessage(text, 'user');
        this.input.value = '';
        this.autoResize();
        this.updateSendButton();
        
        this.showTyping();
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });
            
            const data = await response.json();
            this.hideTyping();
            
            if (data.response) {
                // Simulate realistic typing delay
                setTimeout(() => {
                    this.addMessage(data.response, 'assistant');
                }, 300);
            } else {
                this.addMessage('connexion perdue', 'system');
            }
        } catch (error) {
            this.hideTyping();
            this.addMessage('réseau indisponible', 'system');
        }
    }
    
    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.style.animationDelay = `${this.messageDelay * 0.1}s`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (type === 'assistant') {
            contentDiv.innerHTML = this.formatMessage(text);
        } else {
            contentDiv.textContent = text;
        }
        
        messageDiv.appendChild(contentDiv);
        this.messages.appendChild(messageDiv);
        
        this.messageDelay++;
        this.scrollToBottom();
        
        // Focus input after message
        if (type === 'assistant') {
            setTimeout(() => this.input.focus(), 100);
        }
    }
    
    formatMessage(text) {
        return text
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br/>');
    }
    
    showTyping() {
        this.isTyping = true;
        this.updateSendButton();
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-message';
        typingDiv.innerHTML = `
            <div class="typing">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        this.messages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTyping() {
        this.isTyping = false;
        this.updateSendButton();
        
        const typingMessage = this.messages.querySelector('.typing-message');
        if (typingMessage) {
            typingMessage.style.opacity = '0';
            typingMessage.style.transform = 'translateY(-10px)';
            setTimeout(() => typingMessage.remove(), 200);
        }
    }
    
    scrollToBottom() {
        requestAnimationFrame(() => {
            this.messages.scrollTo({
                top: this.messages.scrollHeight,
                behavior: 'smooth'
            });
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new FlowChat();
});

// Add touch feedback for mobile
document.addEventListener('touchstart', (e) => {
    if (e.target.matches('#send')) {
        e.target.style.transform = 'scale(0.95)';
    }
});

document.addEventListener('touchend', (e) => {
    if (e.target.matches('#send')) {
        setTimeout(() => {
            e.target.style.transform = '';
        }, 100);
    }
});