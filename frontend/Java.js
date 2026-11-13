
// Store the uploaded image and generated audio
let imageFile = null;
let wavBlob = null;


// Switch between website pages
function page(id) {

    document.querySelectorAll(".page").forEach(section => {
        section.classList.toggle("active", section.id === id);
    });

    document.querySelectorAll(".navlinks button").forEach(button => {
        button.classList.toggle("active", button.dataset.page === id);
    });

    window.scrollTo(0, 0);
}


// Get the uploaded image
document.getElementById("file").addEventListener("change", function(event) {

    loadImage(event.target.files[0]);

});


// Display the uploaded image
function loadImage(file) {

    if (!file) return;

    if (file.type !== "image/png" && file.type !== "image/jpeg") {
        alert("Please choose a PNG or JPG image.");
        return;
    }

    imageFile = file;

    let imageURL = URL.createObjectURL(file);

    document.getElementById("preview").innerHTML =
        `<img src="${imageURL}" alt="Uploaded Earth image">`;

    document.getElementById("meta").textContent =
        file.name + " - " + (file.size / 1048576).toFixed(2) + " MB";

    document.getElementById("generate").disabled = false;

    document.getElementById("audioPanel").hidden = true;
}


// Generate sound from the image
async function makeSound() {

    if (!imageFile) return;

    // Read the image
    let image = await createImageBitmap(imageFile);

    let canvas = document.createElement("canvas");

    canvas.width = 96;
    canvas.height = 64;

    let context = canvas.getContext("2d");

    context.drawImage(image, 0, 0, 96, 64);

    let pixels = context.getImageData(0, 0, 96, 64).data;

    let brightness = [];

    // Calculate the average brightness of each column
    for (let column = 0; column < 96; column++) {

        let total = 0;

        for (let row = 0; row < 64; row++) {

            let position = (row * 96 + column) * 4;

            let red = pixels[position];
            let green = pixels[position + 1];
            let blue = pixels[position + 2];

            total += 0.2126 * red + 0.7152 * green + 0.0722 * blue;
        }

        brightness.push(total / 64);
    }


    // Convert brightness into sound
    let sampleRate = 22050;

    let samplesPerColumn = Math.floor(sampleRate * 0.075);

    let samples = new Float32Array(samplesPerColumn * 96);

    for (let column = 0; column < 96; column++) {

        let frequency = 180 + brightness[column] / 255 * 620;

        for (let i = 0; i < samplesPerColumn; i++) {

            let fade = Math.min(1, i / 180, (samplesPerColumn - i) / 180);

            samples[column * samplesPerColumn + i] =
                0.2 * Math.sin(2 * Math.PI * frequency * i / sampleRate)
                * Math.max(0, fade);
        }
    }


    // Create the WAV audio file
    wavBlob = createWAV(samples, sampleRate);

    let audioURL = URL.createObjectURL(wavBlob);

    document.getElementById("download").href = audioURL;


    // Display the brightness chart
    let chart = document.getElementById("chart");

    chart.innerHTML = "";

    brightness.forEach(value => {

        let bar = document.createElement("div");

        bar.className = "bar";

        bar.style.height = Math.max(3, value / 255 * 100) + "%";

        chart.appendChild(bar);
    });


    // Show the audio controls
    document.getElementById("audioPanel").hidden = false;
}


// Convert sound samples into a WAV file
function createWAV(samples, sampleRate) {

    let buffer = new ArrayBuffer(44 + samples.length * 2);

    let view = new DataView(buffer);

    function writeText(position, text) {

        for (let i = 0; i < text.length; i++) {
            view.setUint8(position + i, text.charCodeAt(i));
        }
    }

    writeText(0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);

    writeText(8, "WAVE");
    writeText(12, "fmt ");

    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);

    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);

    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);

    writeText(36, "data");
    view.setUint32(40, samples.length * 2, true);


    // Store the audio samples
    for (let i = 0; i < samples.length; i++) {

        let value = Math.max(-1, Math.min(1, samples[i]));

        let audioValue = value < 0 ? value * 32768 : value * 32767;

        view.setInt16(44 + i * 2, audioValue, true);
    }

    return new Blob([buffer], { type: "audio/wav" });
}


// Play the generated audio
function playSound() {

    if (!wavBlob) return;

    let audioURL = URL.createObjectURL(wavBlob);

    let audio = new Audio(audioURL);

    audio.play().catch(() => {
        alert("Could not play audio. Please try again.");
    });
}
