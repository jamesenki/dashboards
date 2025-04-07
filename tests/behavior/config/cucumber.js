module.exports = {
  default: {
    paths: ['tests/behavior/features/**/*.feature', 'features/**/*.feature'],
    require: [
      'tests/behavior/step_definitions/**/*.js',
      'tests/behavior/support/**/*.js',
      'features/step_definitions/**/*.js',
      'features/support/**/*.js'
    ],
    format: [
      'progress',
      'html:tests/behavior/reports/cucumber-report.html',
      'json:tests/behavior/reports/cucumber-report.json',
    ],
    publishQuiet: true,
    parallel: 3
  },
  realtime: {
    paths: ['features/realtime_updates.feature'],
    require: [
      'features/support/world.js',
      'features/support/hooks.js',
      'features/step_definitions/shadow_document_steps.js',
      'features/step_definitions/realtime_updates_steps.js'
    ],
    format: [
      'progress',
      'html:tests/behavior/reports/realtime-report.html',
      'json:tests/behavior/reports/realtime-report.json',
    ],
    publishQuiet: true
  },
  current: {
    paths: ['tests/behavior/features/**/*.feature'],
    require: [
      'tests/behavior/step_definitions/**/*.js',
      'tests/behavior/support/**/*.js'
    ],
    format: [
      'progress',
      'html:tests/behavior/reports/cucumber-current-report.html',
      'json:tests/behavior/reports/cucumber-current-report.json',
    ],
    tags: '@current and not @wip',
    publishQuiet: true,
    parallel: 3
  },
  future: {
    paths: ['tests/behavior/features/**/*.feature'],
    require: [
      'tests/behavior/step_definitions/**/*.js',
      'tests/behavior/support/**/*.js'
    ],
    format: [
      'progress',
      'html:tests/behavior/reports/cucumber-future-report.html',
      'json:tests/behavior/reports/cucumber-future-report.json',
    ],
    tags: '@future',
    publishQuiet: true,
    dryRun: true // Don't actually run tests, just check if steps match
  }
}
