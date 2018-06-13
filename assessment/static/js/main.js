var element  = document.getElementById("time_left")
var bar = document.getElementById('bar');
if (element) {
    setTimeLeft()
    var x = setInterval(function() {
      distance -= 10;
      if (distance < 0) {
        clearInterval(x);
        element.innerHTML = _["Vaqt Tugadi"];
      }
    }, 10000);
}
function timeToString(time) {
    if (time>0){
        var hours = Math.floor(time / 3600);
        var minutes = Math.floor(time / 60) % 60;
        return (hours ? hours + _[" soat "]:"") + minutes + _[" daqiqa"];
    } else {
        return;
    }
}
function check() {
    var checkboxes = document.querySelectorAll('input[type="checkbox"], input[type="radio"');
    var checkedOne = Array.prototype.slice.call(checkboxes).some(x => x.checked);
    if (!checkedOne){
        document.getElementById('valErr').innerHTML = _["Iltimos Javobingizni tanlang"];
        return false;
    }
    return true;
}

function setTimeLeft(){

    bar.style.width = Math.min(1-distance/testTime, 1) * 100 + "%";
    element.innerHTML = timeToString(distance) ? _[`$(timeToString(distance)) vaqtingiz qoldi] : _["Vaqt Tugadi"];
}

setTimeLeft()

var _ = {

}