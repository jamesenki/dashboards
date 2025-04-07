/**
 * Utility script to find undefined step definitions
 * Following TDD principles - ensure all expected behaviors are defined before implementation
 */
const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Helper function to extract step patterns from step files
function extractDefinedSteps(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const stepRegex = /(Given|When|Then)\(['"](.*?)['"],/g;
  
  const steps = [];
  let match;
  while ((match = stepRegex.exec(content)) !== null) {
    steps.push({
      type: match[1],
      pattern: match[2],
      file: path.basename(filePath)
    });
  }
  
  return steps;
}

// Helper function to extract steps from feature files
function extractFeatureSteps(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const stepRegex = /(Given|When|Then|And) (.*?)$/gm;
  
  const steps = [];
  let match;
  while ((match = stepRegex.exec(content)) !== null) {
    let step = match[2].trim();
    // Remove quotes from parameters
    step = step.replace(/"([^"]*)"/g, '{string}');
    steps.push({
      type: match[1],
      step,
      file: path.basename(filePath),
      line: content.substring(0, match.index).split('\n').length
    });
  }
  
  return steps;
}

// Find all step definition files
const stepFiles = glob.sync(path.join(__dirname, 'features/step_definitions/**/*.js'));
const definedSteps = [];

stepFiles.forEach(file => {
  const steps = extractDefinedSteps(file);
  definedSteps.push(...steps);
});

// Find all feature files
const featureFiles = glob.sync(path.join(__dirname, 'features/**/*.feature'));
const featureSteps = [];

featureFiles.forEach(file => {
  const steps = extractFeatureSteps(file);
  featureSteps.push(...steps);
});

// Check for undefined steps
console.log('Checking for undefined steps...');
const undefinedSteps = [];

featureSteps.forEach(featureStep => {
  // Skip background steps as they often have special handling
  if (featureStep.step.includes('Background:')) return;
  
  // Convert And steps to their real type
  let stepType = featureStep.type;
  if (stepType === 'And') {
    // Assume the same type as the previous step (simplification)
    stepType = 'Then'; // default fallback
  }
  
  // Check if step is defined
  const isDefined = definedSteps.some(definedStep => {
    // Check if pattern matches
    const pattern = definedStep.pattern;
    const regexStr = pattern
      .replace(/\(/g, '\\(')
      .replace(/\)/g, '\\)')
      .replace(/\{string\}/g, '"([^"]*)"')
      .replace(/\{word\}/g, '(\\S+)')
      .replace(/\{int\}/g, '(\\d+)');
    
    const regex = new RegExp(`^${regexStr}$`);
    return regex.test(featureStep.step);
  });
  
  if (!isDefined) {
    undefinedSteps.push(featureStep);
  }
});

if (undefinedSteps.length === 0) {
  console.log('All steps are defined!');
} else {
  console.log(`Found ${undefinedSteps.length} undefined steps:`);
  undefinedSteps.forEach(step => {
    console.log(`${step.file}:${step.line} - ${step.type} ${step.step}`);
  });
}

// Print duplicate step definitions
console.log('\nChecking for duplicate step definitions...');
const patternCount = {};

definedSteps.forEach(step => {
  const pattern = step.pattern;
  if (!patternCount[pattern]) {
    patternCount[pattern] = [];
  }
  patternCount[pattern].push(step.file);
});

let duplicateFound = false;
Object.entries(patternCount).forEach(([pattern, files]) => {
  if (files.length > 1) {
    duplicateFound = true;
    console.log(`"${pattern}" is defined multiple times:`);
    files.forEach(file => console.log(`  - ${file}`));
  }
});

if (!duplicateFound) {
  console.log('No duplicate step definitions found!');
}
