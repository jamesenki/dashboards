# Test Driven Development: Red, Green, Refactor

Test Driven Development (TDD) is a software development approach where tests are written before the actual implementation code. The process follows three key steps known as "Red, Green, Refactor."

## Core TDD Cycle

### 1. Red: Write a Failing Test
- Start by writing a test that defines the functionality you want to implement
- The test should fail when run (hence "red" - like a failing test in a test runner)
- This step clarifies what you're trying to achieve before writing any implementation

### 2. Green: Write Minimal Code to Pass the Test
- Write just enough code to make the test pass
- Focus on functionality, not elegance or optimization
- When the test passes (goes "green"), you have working code that meets your defined requirements

### 3. Refactor: Improve Code Quality
- Clean up your implementation while keeping tests passing
- Remove duplication, improve naming, and enhance design
- Ensure tests still pass after refactoring to verify functionality is preserved

This cycle is repeated for each feature or component, gradually building up the system with thorough test coverage.

## Benefits of TDD
- Ensures high test coverage
- Clarifies requirements before implementation
- Provides instant feedback on code changes
- Creates more modular, decoupled designs
- Builds confidence in code correctness
- Serves as living documentation

## TDD in AI and ML Applications

Applying TDD to AI/ML development requires some adaptations but follows the same principles:

### 1. Red: Define Expected ML Behavior
- Write tests for model inputs and expected outputs
- Define performance metrics and thresholds (accuracy, F1-score, etc.)
- Create tests for data preprocessing and feature engineering
- Specify edge cases and corner cases the model should handle

```python
def test_sentiment_classifier():
    classifier = SentimentClassifier()
    positive_text = "I love this product, it's amazing!"
    assert classifier.predict(positive_text) > 0.8  # Should predict positive with high confidence
    
    negative_text = "This is terrible, I hate it."
    assert classifier.predict(negative_text) < 0.2  # Should predict negative with high confidence
```

### 2. Green: Implement ML Solution
- Develop model architecture
- Train the model with appropriate data
- Tune hyperparameters until tests pass
- Implement required preprocessing steps

### 3. Refactor: Optimize ML Pipeline
- Improve model efficiency
- Enhance feature engineering
- Reduce computational complexity
- Streamline data pipelines while maintaining performance metrics

## ML-Specific Testing Approaches

### Data Testing
```python
def test_training_data_quality():
    data = load_training_data()
    assert not data.isna().any().any()  # No missing values
    assert len(data) >= 1000  # Sufficient training examples
    assert data['label'].value_counts().min() >= 100  # Minimum samples per class
```

### Model Performance Testing
```python
def test_model_performance():
    model = TrainedModel()
    X_test, y_test = load_test_data()
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    assert accuracy >= 0.85  # Minimum acceptable accuracy
```

### Model Robustness Testing
```python
def test_model_robustness():
    model = TrainedModel()
    perturbed_inputs = generate_adversarial_examples(test_inputs)
    original_predictions = model.predict(test_inputs)
    perturbed_predictions = model.predict(perturbed_inputs)
    consistency = np.mean(original_predictions == perturbed_predictions)
    assert consistency >= 0.7  # Model should be somewhat robust to perturbations
```

## Challenges in ML TDD

1. **Non-determinism**: ML models may produce slightly different results each run
   - Solution: Use statistical assertions and confidence intervals instead of exact matches
2. **Complex dependencies**: ML systems often have complex data pipelines
   - Solution: Mock external dependencies and use small, synthetic datasets for unit tests
3. **Resource intensity**: Training models is computationally expensive
   - Solution: Use smaller models or datasets for unit tests, full tests in CI/CD pipeline
4. **Evolving requirements**: ML performance targets might change as you learn more
   - Solution: Parameterize tests and make thresholds configurable

## Practical TDD ML Example

Let's develop a simple text classifier using TDD:

### Step 1: Red - Write failing tests
```python
def test_text_classifier_initialization():
    classifier = TextClassifier(categories=['sports', 'politics', 'technology'])
    assert hasattr(classifier, 'predict')
    assert classifier.categories == ['sports', 'politics', 'technology']

def test_text_classifier_prediction():
    classifier = TextClassifier(categories=['sports', 'politics'])
    sports_text = "The team won the championship with a last-minute goal"
    politics_text = "The senate will vote on the new bill tomorrow"
    
    assert classifier.predict(sports_text) == 'sports'
    assert classifier.predict(politics_text) == 'politics'
```

### Step 2: Green - Implement minimal solution
```python
class TextClassifier:
    def __init__(self, categories):
        self.categories = categories
        self.vectorizer = CountVectorizer()
        self.model = MultinomialNB()
        self._is_trained = False
        
    def train(self, texts, labels):
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        self._is_trained = True
        
    def predict(self, text):
        if not self._is_trained:
            # For test purposes only, predict based on keywords
            if 'goal' in text or 'team' in text or 'championship' in text:
                return 'sports'
            elif 'senate' in text or 'vote' in text or 'bill' in text:
                return 'politics'
            return self.categories[0]
            
        X = self.vectorizer.transform([text])
        return self.model.predict(X)[0]
```

### Step 3: Refactor - Improve implementation
```python
class TextClassifier:
    def __init__(self, categories):
        self.categories = categories
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.model = LinearSVC()
        self._is_trained = False
        
    def train(self, texts, labels):
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        self._is_trained = True
        
    def predict(self, text):
        if not self._is_trained:
            raise ValueError("Model must be trained before prediction")
            
        X = self.vectorizer.transform([text])
        return self.model.predict(X)[0]
        
    def evaluate(self, test_texts, test_labels):
        X_test = self.vectorizer.transform(test_texts)
        predictions = self.model.predict(X_test)
        return classification_report(test_labels, predictions)
```

By following this cycle, you build ML applications that are well-tested, meet requirements, and are easier to maintain and enhance over time.

## Best Practices for Test Creation and Modification

### Core Principles from TDD Thought Leaders

#### Kent Beck (Creator of TDD)
- **Tests as Documentation**: "Tests should serve as living documentation that explains what your code does."
- **Isolated Tests**: "Make each test independent of all others. Each test should be able to run alone."
- **One Assert Per Test**: "Ideally, each test should verify just one behavior to make failures clear and specific."
- **Fast Tests**: "Tests should run quickly - slow tests won't be run often enough to be useful."

#### Dave Farley (Continuous Delivery Expert)
- **Tests as Executable Specifications**: "Write tests that describe desired behavior, not implementation details."
- **Test Behavior, Not Methods**: "Structure tests around behaviors that deliver value, not individual methods."
- **No Test Logic**: "Tests should be straightforward with no conditional logic, loops, or complex algorithms."
- **Test First, Always**: "The moment you write code without tests, you've created a maintenance burden."

#### Robert C. Martin (Uncle Bob)
- **Clean Tests**: "Test code should be maintained with the same care as production code."
- **F.I.R.S.T Principles**:
   - Fast: Tests should run quickly
   - Independent: Tests shouldn't depend on each other
   - Repeatable: Tests should produce the same results in any environment
   - Self-validating: Tests should have a boolean output
   - Timely: Tests should be written just before the code that makes them pass

### Preserving Tests as Source of Truth

1. **Don't Change Tests Just to Make Them Pass**
   - Tests should represent requirements, not implementation
   - When code changes break tests, evaluate whether the requirement changed
   - If implementation changed but requirements didn't, fix the code, not the test

2. **Separate Configuration from Test Logic**
   - Extract environment-specific parameters into configuration files
   - Use dependency injection to provide test doubles for external dependencies
   - Keep test assertion logic separate from setup and configuration

3. **Explicit Setup and Teardown**
   - Make test dependencies explicit in setup methods
   - Clean up all side effects in teardown to ensure test isolation
   - Use test fixtures and factories to standardize object creation

4. **Version Control Test Data With Code**
   - Keep test data in version control alongside tests
   - Use small, purpose-built test datasets rather than production samples
   - Document the meaning and purpose of test data

5. **Test at the Right Level**
   - Unit tests: Test one unit (class/function) in isolation
   - Integration tests: Test how components work together
   - End-to-end tests: Test complete features from user perspective
   - Match test type to what you need to verify

6. **Test Boundaries and Edge Cases**
   - Test both normal and edge cases systematically
   - Consider inputs at, just below, and just above boundaries
   - Test empty, null, maximum, and minimum inputs explicitly

### Handling Test Modifications

When faced with failing tests after code changes:

1. **Ask "Why?"**
   - Is the requirement truly changing, or is it implementation drift?
   - Is the test too coupled to implementation details?

2. **Refactor Tests When Needed**
   - Separate test modification from behavior change
   - First refactor tests to be more robust without changing assertions
   - Then make your implementation changes

3. **Evolve Tests with Requirements**
   - When requirements change, modify tests first
   - Make tests fail for the right reasons before fixing them
   - Keep test history to document requirement evolution

4. **Consider Test Smells**
   - Fragile tests often indicate design problems
   - If tests break often, they may be too coupled to implementation
   - Use test failures as design feedback

As Martin Fowler notes: "If it's difficult to write tests, it's a sign that your design needs improvement. Tests not only verify your code but give you feedback on your design."
