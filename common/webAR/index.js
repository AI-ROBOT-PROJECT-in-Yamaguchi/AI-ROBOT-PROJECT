var scene = document.querySelector('a-scene');
var cylinder = document.createElement('a-box');
cylinder.setAttribute('color', '#FF9500');
cylinder.setAttribute('height', '2');
cylinder.setAttribute('position', '0 0 -3');
scene.appendChild(cylinder);

var t = 0;
function render() {
	t += 0.01;
	requestAnimationFrame(render);
	cylinder.setAttribute('position', '0 '+(Math.sin(t*2)+1)+' -3');
}

function saveCanvas(canvas_id)
{
	var canvas = document.getElementById(canvas_id);
	console.log("canvas:");
	console.log(canvas);
	//アンカータグを作成
	var a = document.createElement('a');
	//canvasをJPEG変換し、そのBase64文字列をhrefへセット
	a.href = canvas.toDataURL('image/jpeg', 0.85);
	//ダウンロード時のファイル名を指定
	a.download = 'download.jpg';
	//クリックイベントを発生させる
	a.click();
}

render();

//saveCanvas("container");

console.log("t:");
console.log(t);
var canvas = document.getElementById('container');
console.log("canvas:");
console.log(canvas);
var context = canvas.getContext('2d');
console.log("context:");
console.log(context);

var imgData = context.getImageData(0, 0, 32, 32);
console.log("img");
console.log(imgData[0]);
console.log(imgData[1]);