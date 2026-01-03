// src/routes/analysis.js
const express = require('express');
const router = express.Router();
const AIService = require('../services/aiService');
const DecisionEngine = require('../services/decisionEngine');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

// Configure multer
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, '../../uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueName = Date.now() + '_' + file.originalname;
    cb(null, uniqueName);
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: 5 * 1024 * 1024,
    files: 1
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('Only images (jpeg, jpg, png) are allowed'));
    }
  }
});

const aiService = new AIService();

// MAIN ANALYSIS ENDPOINT
router.post('/', upload.single('image'), async (req, res, next) => {
  console.log('🌿 === INTELLIGENT ANALYSIS REQUEST ===');
  
  try {
    if (!req.file) {
      console.error('❌ No file uploaded');
      return res.status(400).json({
        success: false,
        error: 'No image file received'
      });
    }

    console.log(`📸 File: ${req.file.originalname}`);

    // Parse sensor data
    let sensorData = {};
    if (req.body.sensorData) {
      try {
        sensorData = JSON.parse(req.body.sensorData);
        console.log('📊 Sensor data:', sensorData);
      } catch (e) {
        console.warn('⚠️ Could not parse sensorData:', e.message);
      }
    }

    // Step 1: AI Visual Analysis
    console.log('🔍 Step 1: CNN Visual Analysis...');
    let aiResult;
    try {
      aiResult = await aiService.analyzeImage(req.file.path);
      console.log(`✅ CNN sees: ${aiResult.prediction} (${(aiResult.confidence * 100).toFixed(1)}% confidence)`);
    } catch (aiError) {
      console.error('❌ AI failed:', aiError.message);
      aiResult = aiService.mockImageAnalysis();
      console.log('🎭 Using mock analysis');
    }

    // Step 2: Intelligent Diagnosis
    console.log('🧠 Step 2: Intelligent Diagnosis Engine...');
    const decisionEngine = new DecisionEngine();
    const intelligentAnalysis = decisionEngine.analyzeSituation(aiResult, sensorData);

    // Build comprehensive response
    const response = {
      success: true,
      mode: aiResult.test_mode ? 'mock' : 'ai',
      timestamp: new Date().toISOString(),
      image: req.file.filename,
      
      // 1. VISUAL ASSESSMENT
      visualAssessment: {
        cnnPrediction: aiResult.prediction,
        confidence: aiResult.confidence,
        confidencePercentage: (aiResult.confidence * 100).toFixed(1),
        message: intelligentAnalysis.visualAssessment.message,
        possibleIssues: aiResult.possible_issues || []
      },
      
      // 2. SENSOR READINGS
      sensorReadings: {
        raw: sensorData,
        assessment: intelligentAnalysis.sensorAssessment,
        calculatedNPK: intelligentAnalysis.sensorAssessment.calculatedNPK,
        issues: intelligentAnalysis.sensorAssessment.issues.map(issue => ({
          sensor: issue.sensor,
          value: issue.value,
          unit: issue.unit,
          optimalRange: `${issue.min}-${issue.max}${issue.unit}`,
          status: issue.severity === 'low' ? 'too_low' : 'too_high'
        }))
      },
      
      // 3. INTELLIGENT DIAGNOSIS (THE VERDICT)
      intelligentDiagnosis: {
        emergencyLevel: intelligentAnalysis.emergencyLevel,
        verdict: intelligentAnalysis.intelligentDiagnosis.verdict,
        confidence: intelligentAnalysis.intelligentDiagnosis.confidence,
        message: intelligentAnalysis.intelligentDiagnosis.message,
        reasoning: intelligentAnalysis.intelligentDiagnosis.reasoning,
        requiresImmediateAction: intelligentAnalysis.intelligentDiagnosis.requiresImmediateAction
      },
      
      // 4. SPECIFIC DEFICIENCIES DETECTED
      deficiencies: intelligentAnalysis.deficiencies,
      
      // 5. ACTIONABLE RECOMMENDATIONS
      recommendations: {
        emergencyLevel: intelligentAnalysis.emergencyLevel.level,
        priorityOrder: intelligentAnalysis.recommendations.map((rec, index) => ({
          step: index + 1,
          action: rec.action,
          reason: rec.reason,
          icon: rec.icon,
          priority: rec.priority
        })),
        totalSteps: intelligentAnalysis.recommendations.length
      },
      
      // 6. WHAT TO DO NEXT
      nextSteps: intelligentAnalysis.nextSteps,
      
      // Legacy support
      finalDiagnosis: {
        health: aiResult.prediction,
        confidence: aiResult.confidence,
        message: intelligentAnalysis.intelligentDiagnosis.message
      }
    };

    console.log('✅ === INTELLIGENT ANALYSIS COMPLETE ===');
    console.log(`📋 Verdict: ${intelligentAnalysis.intelligentDiagnosis.verdict}`);
    console.log(`🚨 Emergency Level: ${intelligentAnalysis.emergencyLevel.level.toUpperCase()}`);
    console.log(`📝 Recommendations: ${intelligentAnalysis.recommendations.length} actionable steps`);
    
    res.json(response);

  } catch (error) {
    console.error('💥 Route error:', error);
    next(error);
  }
});

// Health check
router.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    route: 'analysis',
    timestamp: new Date().toISOString() 
  });
});

module.exports = router;