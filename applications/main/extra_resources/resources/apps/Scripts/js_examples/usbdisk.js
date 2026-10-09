// Script cannot work without usbdisk module so check before
checkSdkFeatures(["usbdisk"]);

let usbdisk = require("usbdisk");
let storage = require("storage");

let imagePath = "/ext/apps_data/mass_storage/128MB.img";
let imageSize = 128 * 1024 * 1024;

let imageExisted = storage.fileExists(imagePath);
if (imageExisted) {
    print("Obraz disku '128MB' uz existuje");
} else {
    // CreateImage isn't necessary to overall function, check when its used not at script start
    if (doesSdkSupport(["usbdisk-createimage"])) {
        print("Vytvarim obraz disku '128MB'...");
        usbdisk.createImage(imagePath, imageSize);
    } else {
        die("Obraz disku '128MB' neexistuje a nelze ho automaticky vytvorit");
    }
}

print("Spoustim UsbDisk...");
usbdisk.start("/ext/apps_data/mass_storage/128MB.img");

print("Spusteno, cekam na vysunuti...");
while (!usbdisk.wasEjected()) {
    delay(1000);
}

print("Vysunuto, zastavuji UsbDisk...");
usbdisk.stop();

if (!imageExisted) {
    print("Odstranuji obraz disku...");
    storage.remove(imagePath);
}

print("Hotovo");