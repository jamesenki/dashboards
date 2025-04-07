import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

// Dashboard Components
import { WaterHeaterDashboardComponent } from './components/dashboard/water-heater-dashboard.component';
import { DeviceStatusCardComponent } from './components/dashboard/device-status-card.component';
import { TelemetryHistoryChartComponent } from './components/dashboard/telemetry-history-chart.component';
import { DevicePerformanceMetricsComponent } from './components/dashboard/device-performance-metrics.component';
import { DeviceDetailsComponent } from './components/dashboard/device-details.component';
import { AnomalyAlertsComponent } from './components/dashboard/anomaly-alerts.component';

// Shared Components
// (These would typically be imported from a shared module)

// Dashboard Routes
const routes: Routes = [
  { 
    path: 'dashboard', 
    children: [
      { path: '', redirectTo: 'water-heaters', pathMatch: 'full' },
      { path: 'water-heaters', component: WaterHeaterDashboardComponent },
      { path: 'water-heaters/:id', component: DeviceDetailsComponent }
    ] 
  }
];

/**
 * Dashboard Module
 * 
 * Contains all dashboard-related components for device monitoring and control.
 * This module is designed to be device-agnostic at its core, with device-specific
 * implementations extending the core functionality.
 */
@NgModule({
  declarations: [
    WaterHeaterDashboardComponent,
    DeviceStatusCardComponent,
    TelemetryHistoryChartComponent,
    DevicePerformanceMetricsComponent,
    DeviceDetailsComponent,
    AnomalyAlertsComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    HttpClientModule,
    RouterModule.forChild(routes)
  ],
  exports: [
    WaterHeaterDashboardComponent,
    AnomalyAlertsComponent,
    DeviceStatusCardComponent,
    TelemetryHistoryChartComponent,
    DevicePerformanceMetricsComponent,
    RouterModule
  ]
})
export class DashboardModule { }
