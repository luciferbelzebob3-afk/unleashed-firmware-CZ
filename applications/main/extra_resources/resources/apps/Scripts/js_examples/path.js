let storage = require("storage");

print("adresar skriptu (__dirname): " + __dirname);
print("soubor skriptu (__filename): " + __filename);
if (storage.fileExists(__dirname + "/math.js")) {
    print("soubor math.js je tady.");
} else {
    print("soubor math.js tu neni.");
}
