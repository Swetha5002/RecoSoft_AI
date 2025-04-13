document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Smooth scroll animation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Add animation to elements when they come into view
    const animateOnScroll = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-slide-up');
                entry.target.style.opacity = 1;
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.glass-card, .timeline-event, .stat-card').forEach(el => {
        el.style.opacity = 0;
        animateOnScroll.observe(el);
    });
    
    // Enhanced dropdown interactions
    document.querySelectorAll('.dropdown-toggle').forEach(dropdown => {
        dropdown.addEventListener('show.bs.dropdown', function () {
            this.nextElementSibling.classList.add('animate-scale');
        });
    });
    
    // Add loading states to buttons
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.addEventListener('click', function() {
            if (this.form && this.form.checkValidity()) {
                this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                this.disabled = true;
            }
        });
    });
    
    // Enhanced file upload preview
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const preview = document.getElementById('file-preview');
            if (preview) {
                preview.innerHTML = '';
                [...this.files].forEach(file => {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const div = document.createElement('div');
                        div.className = 'file-preview-item glass-card p-2 mb-2 d-flex align-items-center';
                        div.innerHTML = `
                            <i class="fas fa-file me-2"></i>
                            <span class="flex-grow-1">${file.name}</span>
                            <small class="text-muted">${formatFileSize(file.size)}</small>
                        `;
                        preview.appendChild(div);
                    }
                    reader.readAsDataURL(file);
                });
            }
        });
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    // Add dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        });
        
        // Check for saved dark mode preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
        }
    }
    
    // Handle AJAX file uploads for event attachments
    const attachmentForm = document.getElementById('attachment-form');
    if (attachmentForm) {
        attachmentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const eventId = this.dataset.eventId;
            
            fetch(`/timeline/events/${eventId}/upload/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Add the new attachment to the list
                    const attachmentList = document.getElementById('attachment-list');
                    const newItem = document.createElement('div');
                    newItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                    newItem.innerHTML = `
                        <a href="${data.url}" target="_blank">
                            <i class="fas fa-paperclip me-2"></i> ${data.filename}
                        </a>
                        <button class="btn btn-sm btn-outline-danger delete-attachment" data-id="${data.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    `;
                    attachmentList.appendChild(newItem);
                    
                    // Reset the form
                    this.reset();
                } else {
                    alert('Error uploading file: ' + (data.errors || data.error));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while uploading the file.');
            });
        });
    }
    
    // Handle attachment deletion
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-attachment')) {
            const attachmentId = e.target.dataset.id;
            if (confirm('Are you sure you want to delete this attachment?')) {
                fetch(`/timeline/attachments/${attachmentId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        e.target.closest('.list-group-item').remove();
                    } else {
                        alert('Error deleting attachment');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while deleting the attachment.');
                });
            }
        }
    });
    
    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});