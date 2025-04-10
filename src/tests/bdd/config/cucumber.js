module.exports = {
  default: {
    paths: [
      'src/tests/bdd/features/**/*.feature'
    ],
    require: [
      'src/tests/bdd/steps/**/*.js',
      'features/step_definitions/**/*.js'  // Include existing step definitions
    ],
    format: [
      'progress',
      'html:src/tests/bdd/test-reports/cucumber-report.html'
    ],
    formatOptions: {
      snippetInterface: 'async-await'
    },
    publish: false
  }
};
