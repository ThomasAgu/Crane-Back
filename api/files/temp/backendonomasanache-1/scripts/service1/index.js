const fs = require("fs");
const os = require("os");

console.log("==================================");
console.log("Container started successfully");
console.log("==================================");

console.log("Node:", process.version);
console.log("Hostname:", os.hostname());
console.log("Working directory:", process.cwd());

console.log("\nCurrent directory contents:");
console.log(fs.readdirSync("."));

console.log("\nReading files:");

for (const file of fs.readdirSync(".")) {
    if (fs.statSync(file).isFile()) {
        console.log(`\n----- ${file} -----`);
        try {
            console.log(fs.readFileSync(file, "utf8"));
        } catch {
            console.log("<binary>");
        }
    }
}

setInterval(() => {
    console.log("Still alive:", new Date().toISOString());
}, 5000);