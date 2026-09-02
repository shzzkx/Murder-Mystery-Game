var i = 0;
var txt = document.getElementByClass("text");
var speed = 50;

function typeWriter() {
  if (i < txt.length) {
    document.getElementByClass("text").innerHTML += txt.charAt(i);
    i++;
    setTimeout(typeWriter, speed);
  }
  document.getElementByClass(":not(.text)").innerHTML = document.getElementByClass(":not(.text)");
}

document.addEventListener("DOMContentLoaded", function() {
  typeWriter();
});
