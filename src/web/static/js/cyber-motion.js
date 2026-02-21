document.addEventListener('DOMContentLoaded', () => {
    // 7. Motion Specs: Load Animation
    // Select all major elements to animate in
    const elementsToAnimate = document.querySelectorAll('header, .cyber-panel, .container > *, .footer');
    
    elementsToAnimate.forEach((el, index) => {
        el.classList.add('cyber-enter');
        // Add random horizontal jitter (5%)
        const jitter = (Math.random() * 10 - 5) + 'px';
        el.style.setProperty('--jitter', jitter);
        // Stagger delays
        el.style.animationDelay = `${index * 0.1}s`;
    });

    // 3. Interaction Feedback: Click Flash
    const clickables = document.querySelectorAll('a, button, .btn, .drop-zone, input[type="file"]');
    
    clickables.forEach(el => {
        el.addEventListener('click', (e) => {
            // Remove class if it exists to restart animation
            el.classList.remove('glitch-active');
            void el.offsetWidth; // Trigger reflow
            el.classList.add('glitch-active');
            
            // Remove after animation completes (0.1s)
            setTimeout(() => {
                el.classList.remove('glitch-active');
            }, 100);
        });
    });

    // 7. Scroll Glitch Effect
    // Create an observer for scroll entry
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px'
    };

    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Trigger RGB split glitch
                entry.target.classList.add('scroll-glitch');
                // Remove after animation to allow re-triggering if needed (or keep it one-off)
                // Requirement says "trigger once", so unobserve
                scrollObserver.unobserve(entry.target);
                
                setTimeout(() => {
                    entry.target.classList.remove('scroll-glitch');
                }, 200); // 0.2s duration matches CSS
            }
        });
    }, observerOptions);

    // Observe structural elements
    document.querySelectorAll('section, .cyber-card, .viewer-container').forEach(el => {
        scrollObserver.observe(el);
    });

    // 6. Decorate Empty Spaces (Random Decals)
    addDecals();

    // --- H1 Title Animation ---
    animateTitle();
});

function addDecals() {
    const container = document.body;
    const decalCount = 5; // Number of random decals
    
    for (let i = 0; i < decalCount; i++) {
        const type = Math.random() > 0.5 ? 'caution' : 'voltage';
        const el = document.createElement('div');
        
        // Random Position (avoiding top/center where main content is)
        const top = Math.random() * 80 + 10 + '%'; // 10-90%
        const left = Math.random() > 0.5 ? Math.random() * 10 + '%' : Math.random() * 10 + 90 + '%'; // Sides
        
        el.style.top = top;
        el.style.left = left;
        el.style.position = 'fixed';
        el.style.zIndex = '-1';
        
        if (type === 'caution') {
            el.className = 'caution-tape';
            el.style.transform = `rotate(${Math.random() * 90 - 45}deg)`;
        } else {
            el.className = 'high-voltage';
            el.innerText = 'HIGH VOLTAGE';
        }
        
        container.appendChild(el);
    }
}

function animateTitle() {
    const titleEl = document.getElementById('animatedTitle');
    if (!titleEl) return;

    const text = titleEl.textContent;
    titleEl.textContent = ''; // Clear original text

    // Split text into spans
    [...text].forEach((char, index) => {
        const span = document.createElement('span');
        span.textContent = char;
        span.className = 'cyber-char';
        
        // Handle spaces to preserve layout
        if (char === ' ') {
            span.style.width = '0.5em';
        }

        // Apply animation delay
        span.style.animationDelay = `${index * 0.1}s`;
        
        titleEl.appendChild(span);
    });
}
