window.addEventListener("DOMContentLoaded", function () {
    const nameInput = document.getElementById("fullname");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const toggleBtn = document.getElementById("togglePassword");
    const form = document.querySelector("form");

    if (nameInput) {
        nameInput.addEventListener("input", () => {
            const value = nameInput.value;
            const nameParts = value.split(/\s+/);
            const capitalized = nameParts.map(word =>
                word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
            ).join(" ");
            const cursorPosition = nameInput.selectionStart;
            nameInput.value = capitalized;
            nameInput.setSelectionRange(cursorPosition, cursorPosition);
        });
    }

    if (emailInput) {
        emailInput.addEventListener("blur", async () => {
            const email = emailInput.value.trim();
            if (email) {
                try {
                    const response = await fetch("/check-email/?email=" + encodeURIComponent(email));
                    const data = await response.json();

                    if (data.exists) {
                        alert("This email is already registered.");
                        emailInput.dataset.exists = "true";
                    } else {
                        emailInput.dataset.exists = "false";
                    }
                } catch (error) {
                    console.error("Email check failed:", error);
                }
            }
        });
    }

    if (form) {
        form.addEventListener("submit", function (e) {
            let isValid = true;
            const name = nameInput.value.trim();
            const emailExists = emailInput.dataset.exists === "true";
            const password = passwordInput.value;


            const words = name.split(/\s+/);
            words.forEach(word => {
                if (word.length <= 2) {
                    isValid = false;
                }
            });

            if (!isValid) {
                alert("Please Enter Your Valid Name.");
            }

            if (emailExists) {
                alert("Email already registered. Please use another email.");
                isValid = false;
            }

            if (password.length < 6) {
                alert("Password must be at least 6 characters long and contain at least one number & one special character.");
                isValid = false;
            } else if (!/\d/.test(password)) {
                alert("Password must contain at least one number.");
                isValid = false;
            } else if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
                alert("Password must contain at least one special character.");
                isValid = false;
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            toggleBtn.textContent = type === 'password' ? 'Show' : 'Hide';
        });
    }
});
