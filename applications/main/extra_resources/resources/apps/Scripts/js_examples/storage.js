let storage = require("storage");
let path = "/ext/storage.test";

print("Soubor existuje:", storage.fileExists(path));

print("Zapisuji...");
let file = storage.openFile(path, "w", "create_always");
file.write("Hello ");
file.close();

print("Soubor existuje:", storage.fileExists(path));

file = storage.openFile(path, "w", "open_append");
file.write("World!");
file.close();

print("Ctu...");
file = storage.openFile(path, "r", "open_existing");
let text = file.read("ascii", 128);
file.close();
print(text);

print("Odstranuji...")
storage.remove(path);

print("Hotovo")

// You don't need to close the file after each operation, this is just to show some different ways to use the API
// There's also many more functions and options, check type definitions in firmware repo