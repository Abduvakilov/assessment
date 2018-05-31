var element  = document.getElementById("time_left")
if (element) {
    var x = setInterval(function() {
      distance -= 10;
      bar.style.width = (1-distance/testTime)*100 + "%";
      element.innerHTML = timeToString(distance) + " vaqtingiz qoldi";
      if (distance < 0) {
        clearInterval(x);
        element.innerHTML = "Vaqt Tugadi";
      }
    }, 10000);
}
function timeToString(time) {
  var hours = Math.floor(time / 3600);
  var minutes = Math.floor(time / 60) % 60;
  return (hours ? hours + " soat ":"") + minutes + " daqiqa";
}
function check() {
    var checkboxes = document.querySelectorAll('input[type="checkbox"], input[type="radio"');
    var checkedOne = Array.prototype.slice.call(checkboxes).some(x => x.checked);
    if (!checkedOne){
        document.getElementById('valErr').innerHTML = "Iltimos Javobingizni tanlang"
        return false;
    }
    return true;
}