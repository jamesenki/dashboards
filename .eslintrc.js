module.exports = {
  "env": {
    "browser": true,
    "es2021": true,
    "node": true,
    "jest": true
  },
  "extends": [
    "eslint:recommended",
    "plugin:prettier/recommended"
  ],
  "parserOptions": {
    "ecmaVersion": 12,
    "sourceType": "module"
  },
  "rules": {
    // Enforce our JavaScript coding standards
    "indent": ["error", 2],
    "linebreak-style": ["error", "unix"],
    "quotes": ["error", "double"],
    "semi": ["error", "always"],
    "camelcase": ["error", { "properties": "always" }],
    "max-len": ["error", { "code": 100 }],
    "no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    
    // Error handling
    "no-console": ["warn", { "allow": ["error", "warn"] }],
    "no-alert": "warn",
    
    // Enforce comments
    "require-jsdoc": ["warn", {
      "require": {
        "FunctionDeclaration": true,
        "MethodDefinition": true,
        "ClassDeclaration": true,
        "ArrowFunctionExpression": false,
        "FunctionExpression": false
      }
    }],
    
    // Enforce modern JavaScript
    "prefer-const": "error",
    "prefer-arrow-callback": "warn",
    "arrow-parens": ["error", "always"],
    "arrow-body-style": ["error", "as-needed"],
    "no-var": "error"
  }
}
