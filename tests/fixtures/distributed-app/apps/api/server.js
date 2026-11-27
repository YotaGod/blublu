const express = require("express");
const app = express();
app.get("/api/health", (req, res) => res.json({ status: "healthy" }));
app.listen(3000);
