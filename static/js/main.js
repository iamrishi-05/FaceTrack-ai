/* ==========================================================================
   FaceTrack AI - Shared Core JavaScript Library
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSidebar();
    initToasts();
});

/**
 * Initialize and handle Dark/Light Theme Switching
 */
function initTheme() {
    const themeBtn = document.getElementById("themeToggleBtn");
    const themeIcon = document.getElementById("themeIcon");
    if (!themeBtn || !themeIcon) return;

    // Set initial icon based on active theme
    const activeTheme = document.documentElement.getAttribute("data-theme") || "dark";
    updateThemeIcon(activeTheme, themeIcon);

    // Toggle click event
    themeBtn.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        
        document.documentElement.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
        updateThemeIcon(newTheme, themeIcon);
        
        // Log event
        console.log(`Theme toggled to: ${newTheme}`);
    });
}

function updateThemeIcon(theme, iconElement) {
    if (theme === "dark") {
        iconElement.className = "bi bi-sun-fill";
    } else {
        iconElement.className = "bi bi-moon-fill";
    }
}

/**
 * Sidebar Navigation Mobile Drawer Controls
 */
function initSidebar() {
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("appSidebar");
    if (!sidebarToggle || !sidebar) return;

    sidebarToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        sidebar.classList.toggle("show");
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", (e) => {
        if (window.innerWidth < 992 && sidebar.classList.contains("show")) {
            if (!sidebar.contains(e.target) && e.target !== sidebarToggle) {
                sidebar.classList.remove("show");
            }
        }
    });
}

/**
 * Handle Auto-dismiss and animations for Toast Alerts
 */
function initToasts() {
    const toasts = document.querySelectorAll(".toast-custom");
    toasts.forEach(toast => {
        // Automatically fade out after 4 seconds
        setTimeout(() => {
            toast.style.transition = "opacity 0.5s ease, transform 0.5s ease";
            toast.style.opacity = "0";
            toast.style.transform = "translateX(50px)";
            
            // Remove from DOM when animation completes
            setTimeout(() => {
                toast.remove();
            }, 500);
        }, 4000);
    });
}

/**
 * Programmatically display a message toast in the UI
 * @param {string} message - The text body of the alert
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
 */
function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-custom glass-card text-${type}`;
    
    let iconClass = "bi-info-circle-fill";
    let borderClr = "var(--color-info)";
    let bgClr = "rgba(59, 130, 246, 0.1)";

    if (type === "success") {
        iconClass = "bi-check-circle-fill";
        borderClr = "var(--color-success)";
        bgClr = "rgba(16, 185, 129, 0.1)";
    } else if (type === "danger" || type === "error") {
        iconClass = "bi-exclamation-triangle-fill";
        borderClr = "var(--color-danger)";
        bgClr = "rgba(239, 68, 68, 0.1)";
        type = "danger"; // Normalize class
        toast.className = `toast-custom glass-card text-danger`;
    } else if (type === "warning") {
        iconClass = "bi-exclamation-circle-fill";
        borderClr = "var(--color-warning)";
        bgClr = "rgba(245, 158, 11, 0.1)";
    }

    toast.style.borderLeft = `4px solid ${borderClr}`;
    toast.style.background = bgClr;
    toast.innerHTML = `
        <i class="bi ${iconClass}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);
    
    // Animate removal
    setTimeout(() => {
        toast.style.transition = "opacity 0.5s ease, transform 0.5s ease";
        toast.style.opacity = "0";
        toast.style.transform = "translateX(50px)";
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}
