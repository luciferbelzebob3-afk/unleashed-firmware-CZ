// Script cannot work without spi module so check before
checkSdkFeatures(["spi"]);

// Connect a w25q32 SPI device to the Flipper Zero.
// D1=pin 2 (MOSI), SLK=pin 5 (SCK), GND=pin 8 (GND), D0=pin 3 (MISO), CS=pin 4 (CS), VCC=pin 9 (3V3)
let spi = require("spi");

// Display textbox so user can scroll to see all output.
let eventLoop = require("event_loop");
let gui = require("gui");
let textBoxView = require("gui/text_box");
let text = "Ukazka SPI\n";
let textBox = textBoxView.makeWith({
    focus: "end",
    font: "text",
    text: text,
});

function addText(add) {
    text += add;
    textBox.set("text", text);
}

gui.viewDispatcher.switchTo(textBox);

// writeRead returns a buffer the same length as the input buffer.
// We send 6 bytes of data, starting with 0x90, which is the command to read the manufacturer ID.
// Can also use Uint8Array([0x90, 0x00, ...]) as write parameter
// Optional timeout parameter in ms. We set to 100ms.
let data_buf = spi.writeRead([0x90, 0x0, 0x0, 0x0, 0x0, 0x0], 100);
let data = Uint8Array(data_buf);
if (data.length === 6) {
    if (data[4] === 0xEF) {
        addText("Nalezeno zarizeni Winbond\n");
        if (data[5] === 0x15) {
            addText("ID zarizeni: W25Q32\n");
        } else {
            addText("Nezname ID zarizeni: " + data[5].toString(16) + "\n");
        }
    } else if (data[4] === 0x0) {
        addText("Pripoj Winbond W25Q32 ke SPI pinum Flipperu Zero.\n");
    } else {
        addText("Nezname zarizeni. ID vyrobce: " + data[4].toString(16) + "\n");
    }
}

addText("\nCtu JEDEC ID\n");

// Acquire the SPI bus. Multiple calls will happen with Chip Select (CS) held low.
spi.acquire();

// Send command (0x9F) to read JEDEC ID.
// Can also use Uint8Array([0x9F]) as write parameter
// Note: you can pass an optional timeout parameter in milliseconds.
spi.write([0x9F]);

// Request 3 bytes of data.
// Note: you can pass an optional timeout parameter in milliseconds.
data_buf = spi.read(3);

// Release the SPI bus as soon as we are done with the set of SPI commands.
spi.release();

data = Uint8Array(data_buf);
addText("ID vyrobce JEDEC: " + data[0].toString(16) + "\n");
addText("Typ pameti JEDEC: " + data[1].toString(16) + "\n");
addText("ID kapacity JEDEC: " + data[2].toString(16) + "\n");

if (data[0] === 0xEF) {
    addText("Nalezeno zarizeni Winbond\n");
}
let capacity = data[1] << 8 | data[2];
if (capacity === 0x4016) {
    addText("Zarizeni: W25Q32\n");
} else if (capacity === 0x4015) {
    addText("Zarizeni: W25Q16\n");
} else if (capacity === 0x4014) {
    addText("Zarizeni: W25Q80\n");
} else {
    addText("Neznama zarizeni\n");
}

// Wait for user to close the app
eventLoop.subscribe(gui.viewDispatcher.navigation, function (_sub, _, eventLoop) {
    eventLoop.stop();
}, eventLoop);

// This script has no interaction, only textbox, so event loop doesn't need to be running all the time
// We run it at the end to accept input for the back button press to quit
// But before that, user sees a textbox and pressing back has no effect
// This is fine because it allows simpler logic and the code above takes no time at all to run
eventLoop.run();
