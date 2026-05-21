require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios'); // Used to talk to the Python server

const app = express();
app.use(cors());
app.use(express.json());

// In production, this points to your deployed Python server (e.g., on Render or Railway)
const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://127.0.0.1:8001';

// -----------------------------------------------------
// PUBLIC ROUTE: This is what your React/HTML frontend calls
// -----------------------------------------------------
app.post('/api/ask-ai', async (req, res) => {
    const { subject, grade, chapter, question } = req.body;

    // 1. You can add User Authentication here later (e.g., check if they are logged in)
    if (!question || !chapter) {
        return res.status(400).json({ error: "Missing required fields." });
    }

    try {
        console.log(`Forwarding question about ${chapter} to Python AI Engine...`);
        
        // 2. Node.js securely calls the Python API
        const pythonResponse = await axios.post(`${PYTHON_SERVICE_URL}/internal/ai/chat`, {
            subject: subject,
            grade: grade,
            chapter: chapter,
            question: question
        });

        // 3. Send the AI's answer back to the frontend student
        return res.json({
            success: true,
            answer: pythonResponse.data.answer
        });

    } catch (error) {
        console.error("Microservice Error:", error.message);
        
        // If Python crashes or sends a 404/500, pass it cleanly to the frontend
        const status = error.response ? error.response.status : 500;
        const message = error.response ? error.response.data.detail : "Python AI service is down.";
        
        return res.status(status).json({ success: false, error: message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Node.js Web Server running on port ${PORT}`);
});