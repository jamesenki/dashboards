import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { BehaviorSubject } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';

import { WaterHeaterDashboardComponent } from './water-heater-dashboard.component';
import { WebSocketService } from '../../services/websocket.service';
import { environment } from '../../../environments/environment';

describe('WaterHeaterDashboardComponent', () => {
  let component: WaterHeaterDashboardComponent;
  let fixture: ComponentFixture<WaterHeaterDashboardComponent>;
  let httpMock: HttpTestingController;
  let mockWebSocketService: jasmine.SpyObj<WebSocketService>;
  let mockConnectionStatus$: BehaviorSubject<boolean>;

  // Mock water heater data for testing
  const mockWaterHeaters = [
    {
      device_id: 'wh-001',
      manufacturer: 'AquaTech',
      model: 'Pro 2000',
      serial_number: 'AT20230001',
      connection_status: 'connected',
      simulated: true,
      state: {
        temperature_current: 120,
        temperature_setpoint: 125,
        heating_status: true
      },
      display_name: 'Kitchen Water Heater'
    },
    {
      device_id: 'wh-002',
      manufacturer: 'HydroMax',
      model: 'Elite 150',
      serial_number: 'HM20230002',
      connection_status: 'connected',
      simulated: false,
      state: {
        temperature_current: 115,
        temperature_setpoint: 120,
        heating_status: false
      }
    },
    {
      device_id: 'wh-003',
      manufacturer: 'AquaTech',
      model: 'Basic 1000',
      serial_number: 'AT20230003',
      connection_status: 'disconnected',
      simulated: false
    }
  ];

  beforeEach(async () => {
    // Create mock for WebSocketService
    mockConnectionStatus$ = new BehaviorSubject<boolean>(true);
    mockWebSocketService = jasmine.createSpyObj('WebSocketService', ['connect']);
    mockWebSocketService.connectionStatus$ = mockConnectionStatus$.asObservable();

    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        FormsModule
      ],
      declarations: [WaterHeaterDashboardComponent],
      providers: [
        { provide: WebSocketService, useValue: mockWebSocketService }
      ],
      schemas: [NO_ERRORS_SCHEMA] // Ignore unknown elements
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(WaterHeaterDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should load water heaters on init', () => {
    // Expect HTTP request to be made
    const req = httpMock.expectOne(`${environment.apiUrl}/api/devices/water-heaters`);
    expect(req.request.method).toBe('GET');
    
    // Respond with mock data
    req.flush(mockWaterHeaters);
    
    // Check if data is correctly processed
    expect(component.waterHeaters.length).toBe(3);
    expect(component.manufacturers).toContain('AquaTech');
    expect(component.manufacturers).toContain('HydroMax');
    expect(component.isLoading).toBeFalse();
    expect(component.lastRefreshed).toBeTruthy();
  });

  it('should handle HTTP error', () => {
    // Expect HTTP request to be made
    const req = httpMock.expectOne(`${environment.apiUrl}/api/devices/water-heaters`);
    
    // Respond with error
    req.flush('Error loading devices', { 
      status: 500, 
      statusText: 'Server Error' 
    });
    
    // Check error handling
    expect(component.isLoading).toBeFalse();
    expect(component.error).toContain('Failed to load water heaters');
  });

  it('should update realTimeActive based on WebSocket connection status', () => {
    // Initial state (set in beforeEach)
    expect(component.realTimeActive).toBeTrue();
    
    // Simulate WebSocket disconnection
    mockConnectionStatus$.next(false);
    expect(component.realTimeActive).toBeFalse();
  });

  it('should apply manufacturer filter correctly', () => {
    // Load mock data
    component.waterHeaters = mockWaterHeaters;
    
    // Apply manufacturer filter
    component.selectedManufacturer = 'AquaTech';
    component.applyFilters();
    
    // Check filtered results
    expect(component.filteredWaterHeaters.length).toBe(2);
    expect(component.filteredWaterHeaters[0].manufacturer).toBe('AquaTech');
    expect(component.filteredWaterHeaters[1].manufacturer).toBe('AquaTech');
  });

  it('should apply connection status filter correctly', () => {
    // Load mock data
    component.waterHeaters = mockWaterHeaters;
    
    // Apply status filter
    component.selectedStatus = 'disconnected';
    component.applyFilters();
    
    // Check filtered results
    expect(component.filteredWaterHeaters.length).toBe(1);
    expect(component.filteredWaterHeaters[0].connection_status).toBe('disconnected');
  });

  it('should apply simulated filter correctly', () => {
    // Load mock data
    component.waterHeaters = mockWaterHeaters;
    
    // Apply simulation filter
    component.showSimulatedOnly = true;
    component.applyFilters();
    
    // Check filtered results
    expect(component.filteredWaterHeaters.length).toBe(1);
    expect(component.filteredWaterHeaters[0].simulated).toBeTrue();
  });

  it('should clear all filters', () => {
    // Set filters
    component.selectedManufacturer = 'AquaTech';
    component.selectedStatus = 'connected';
    component.showSimulatedOnly = true;
    
    // Clear filters
    component.clearFilters();
    
    // Check filters are reset
    expect(component.selectedManufacturer).toBe('');
    expect(component.selectedStatus).toBe('');
    expect(component.showSimulatedOnly).toBeFalse();
  });

  it('should calculate device counts correctly', () => {
    // Load mock data
    component.waterHeaters = mockWaterHeaters;
    
    // Check count calculations
    expect(component.getDeviceCountByStatus('connected')).toBe(2);
    expect(component.getDeviceCountByStatus('disconnected')).toBe(1);
    expect(component.getSimulatedDeviceCount()).toBe(1);
  });

  it('should get correct device display name', () => {
    // Device with display_name
    let device = mockWaterHeaters[0];
    expect(component.getDeviceDisplayName(device)).toBe('Kitchen Water Heater');
    
    // Device without display_name
    device = mockWaterHeaters[1];
    expect(component.getDeviceDisplayName(device))
      .toBe(`HydroMax Elite 150 (wh-002)`);
  });

  it('should refresh data when refresh() is called', () => {
    // Call refresh method
    component.refresh();
    
    // Expect HTTP request to be made
    const req = httpMock.expectOne(`${environment.apiUrl}/api/devices/water-heaters`);
    expect(req.request.method).toBe('GET');
    
    // Fulfill request
    req.flush(mockWaterHeaters);
    
    // Check loading state
    expect(component.isLoading).toBeFalse();
  });
});
