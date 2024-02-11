function togglePasswordVisibility() {
  var passwordField = document.getElementById("passwordField");
  var toggleBtn = document.getElementById("togglePasswordBtn");

  if (passwordField.type === "password") {
      passwordField.type = "text";
      toggleBtn.textContent = "Hide Password";
  } else {
      passwordField.type = "password";
      toggleBtn.textContent = "Show Password";
  }
}
