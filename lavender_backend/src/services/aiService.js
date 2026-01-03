const { PythonShell } = require('python-shell');
const path = require('path');

class AIService {
  constructor() {
    this.pythonScriptPath = path.join(__dirname, '../../python/lavender_ai.py');
    console.log(`🐍 Python script: ${this.pythonScriptPath}`);
  }

  async analyzeImage(imagePath) {
    console.log(`🔍 Calling Python AI with image: ${imagePath}`);
    
    return new Promise((resolve, reject) => {
      const options = {
        mode: 'text',
        pythonPath: 'python',
        pythonOptions: ['-u'],
        scriptPath: path.dirname(this.pythonScriptPath),
        args: [imagePath]
      };

      console.log(`📁 Python script path: ${this.pythonScriptPath}`);
      console.log(`🐍 Python executable: ${options.pythonPath}`);

      const pyshell = new PythonShell(path.basename(this.pythonScriptPath), options);
      let allOutput = '';
      let stderrData = '';

      // Collect ALL output into one string
      pyshell.on('message', (message) => {
        console.log(`🤖 Python line: ${message}`);
        allOutput += message + '\n';
      });

      pyshell.stderr.on('data', (data) => {
        console.log(`🐍 Python stderr: ${data}`);
        stderrData += data;
      });

      pyshell.end((err) => {
        if (err) {
          console.error('❌ Python script execution error:', err);
          return reject(err);
        }

        console.log(`📦 Python script completed. Full output length: ${allOutput.length}`);
        console.log(`📦 Full output:\n${allOutput}`);
        
        if (!allOutput.trim()) {
          console.error('❌ No output from Python script');
          return reject(new Error('No output from Python script'));
        }

        // Find JSON in the output (might be multiple lines)
        try {
          // Try to parse the entire output as JSON
          const result = JSON.parse(allOutput.trim());
          console.log('✅ Successfully parsed complete Python output:', result);
          
          if (result.prediction === 'error') {
            console.error(`❌ Python script reported error: ${result.error}`);
            return reject(new Error(`AI model error: ${result.error}`));
          }
          
          resolve(result);
        } catch (parseError) {
          console.error('❌ Failed to parse as complete JSON:', parseError.message);
          
          // Try to find JSON object in the output
          const jsonMatch = allOutput.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            try {
              const jsonStr = jsonMatch[0];
              console.log('🔍 Found JSON object in output:', jsonStr);
              const result = JSON.parse(jsonStr);
              console.log('✅ Parsed extracted JSON:', result);
              resolve(result);
            } catch (e) {
              console.error('❌ Failed to parse extracted JSON:', e.message);
              reject(new Error(`Invalid JSON from Python: ${e.message}`));
            }
          } else {
            console.error('❌ No JSON object found in output');
            console.error('Raw output:', allOutput);
            reject(new Error('No valid JSON response from Python script'));
          }
        }
      });

      pyshell.on('error', (error) => {
        console.error('❌ Python shell error:', error);
        reject(error);
      });

      setTimeout(() => {
        if (pyshell.terminated) return;
        console.error('⏰ Python script timeout (30 seconds)');
        pyshell.kill();
        reject(new Error('Python script timeout'));
      }, 30000);
    });
  }

  // Mock analysis for testing
  mockImageAnalysis() {
    console.log('🎭 Using mock analysis (fallback mode)');
    const predictions = ['healthy', 'nutrient_deficient', 'diseased'];
    const randomPrediction = predictions[Math.floor(Math.random() * predictions.length)];
    
    return {
      prediction: randomPrediction,
      confidence: 0.7 + Math.random() * 0.25,
      possible_issues: randomPrediction === 'healthy' ? [] : ['test_issue'],
      test_mode: true
    };
  }
}

module.exports = AIService;