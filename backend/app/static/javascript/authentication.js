// Password Toggle Logic
let pw_eye = document.querySelector(".pw_eye");
let eye_close = document.querySelector(".pw_eye_close");
let eye_open = document.querySelector(".pw_eye_open");
let password_input = document.querySelector("#password");
let confirm_password_input = document.querySelector("#confirm_password");

eye_close.style.display = "block";
eye_open.style.display = "none";

pw_eye.addEventListener("click", function () {
    if (eye_close.style.display === "block") {
        eye_close.style.transition = "all 0.4s";
        eye_close.style.display = "none";
        eye_open.style.display = "block";
        password_input.type = "text";
        confirm_password_input.type = "text";
    } else {
        password_input.type = "password";
        confirm_password_input.type = "password";
        eye_close.style.display = "block";
        eye_open.style.display = "none";
    }
});

// Menu Toggle Logic
let menu_bar = document.querySelector(".menu_btn");
let menu_bar_open = document.querySelector(".open_menu");
let menu_bar_close = document.querySelector(".close_menu");

menu_bar_open.style.display = "block";
menu_bar_close.style.display = "none";

menu_bar.addEventListener("click", function () {
    if (menu_bar_open.style.display === "block") {
        menu_bar_open.style.display = "none";
        menu_bar_close.style.display = "block";
    } else {
        menu_bar_open.style.display = "block";
        menu_bar_close.style.display = "none";
    }
});

// Toggle fields based on role selection
function toggleFields(role) {
    document.getElementById('customer_fields').style.display = 'none';
    document.getElementById('professional_fields').style.display = 'none';
    if (role === 'customer') {
        document.getElementById('customer_fields').style.display = 'block';
    } else if (role === 'professional') {
        document.getElementById('professional_fields').style.display = 'block';
    }
}

// Run on DOM load to show correct fields based on selected role
document.addEventListener("DOMContentLoaded", function () {
    const selectedRoleElement = document.querySelector('input[name="role"]:checked');
    if (selectedRoleElement) {
        toggleFields(selectedRoleElement.value);
    }

    // Ensure that role switching works after page load
    document.querySelectorAll('input[name="role"]').forEach((roleRadio) => {
        roleRadio.addEventListener("change", function () {
            toggleFields(this.value);
        });
    });
});