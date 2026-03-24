
let input_username;
let input_password;

document.getElementById("login_button").onclick = function(){

  input_username = document.getElementById("username").value
  input_password = document.getElementById("password").value
  input_username = input_username.replaceAll("<", "&lt;").replaceAll(">", "&gt;")



}
