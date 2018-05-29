var x = setInterval(function() {
  distance -= 10;
  element  = document.getElementById("time_left")
  element.innerHTML = timeToString(distance) + " vaqtingiz qoldi";
  if (distance < 0 || !element) {
    clearInterval(x);
    element.innerHTML = "Vaqt Tugadi";
  }
}, 10000);

function timeToString(time) {
  var hours = Math.floor(time / 3600);
  var minutes = Math.floor(time / 60) % 60;
  return (hours ? hours + " soat ":"") + minutes + " daqiqa";
}