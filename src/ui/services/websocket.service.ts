import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';

/**
 * WebSocket message types
 */
export enum MessageType {
  TELEMETRY = 'telemetry',
  EVENT = 'event',
  COMMAND_RESPONSE = 'command_response',
  SUBSCRIBE = 'subscribe',
  UNSUBSCRIBE = 'unsubscribe',
  COMMAND = 'command'
}

/**
 * Device telemetry message
 */
export interface TelemetryMessage {
  type: MessageType.TELEMETRY;
  device_id: string;
  timestamp: string;
  data: {
    temperature_current?: number;
    temperature_setpoint?: number;
    heating_status?: boolean;
    power_consumption_watts?: number;
    water_flow_gpm?: number;
    mode?: string;
    error_code?: string;
    [key: string]: any;
  };
  simulated: boolean;
}

/**
 * Device event message
 */
export interface EventMessage {
  type: MessageType.EVENT;
  device_id: string;
  event_type: string;
  severity: 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
  details?: any;
  simulated: boolean;
}

/**
 * Command response message
 */
export interface CommandResponseMessage {
  type: MessageType.COMMAND_RESPONSE;
  device_id: string;
  command_id: string;
  command: string;
  status: 'success' | 'error';
  message: string;
  timestamp: string;
  simulated: boolean;
}

/**
 * Union type for all WebSocket messages
 */
export type WebSocketMessage = TelemetryMessage | EventMessage | CommandResponseMessage;

/**
 * WebSocket service for real-time communication with devices
 */
@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket: WebSocket | null = null;
  private reconnectInterval = 5000; // 5 seconds
  private reconnectTimer: any = null;
  private connected = false;
  private clientId: string | null = null;

  // Observable sources
  private connectionStatusSource = new BehaviorSubject<boolean>(false);
  private telemetrySource = new Subject<TelemetryMessage>();
  private eventSource = new Subject<EventMessage>();
  private commandResponseSource = new Subject<CommandResponseMessage>();

  // Observable streams
  public connectionStatus$ = this.connectionStatusSource.asObservable();
  public telemetry$ = this.telemetrySource.asObservable();
  public events$ = this.eventSource.asObservable();
  public commandResponses$ = this.commandResponseSource.asObservable();

  constructor() {
    this.connect();
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.socket) {
      this.socket.close();
    }

    // Clear any existing reconnect timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    const wsUrl = environment.wsUrl || `ws://${window.location.hostname}:8765`;
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('WebSocket connection established');
      this.connected = true;
      this.connectionStatusSource.next(true);
    };

    this.socket.onclose = () => {
      console.log('WebSocket connection closed');
      this.connected = false;
      this.connectionStatusSource.next(false);

      // Attempt to reconnect
      this.reconnectTimer = setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        
        // Process based on message type
        switch (message.type) {
          case MessageType.TELEMETRY:
            this.telemetrySource.next(message as TelemetryMessage);
            break;
          
          case MessageType.EVENT:
            this.eventSource.next(message as EventMessage);
            break;
          
          case MessageType.COMMAND_RESPONSE:
            this.commandResponseSource.next(message as CommandResponseMessage);
            break;
          
          // Handle connection acknowledgment
          case 'connection_ack':
            this.clientId = (message as any).client_id;
            console.log(`Connected with client ID: ${this.clientId}`);
            break;
          
          default:
            console.warn('Unknown message type:', message);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
  }

  /**
   * Close WebSocket connection
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.close();
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Subscribe to updates for a specific device
   * @param deviceId Device ID to subscribe to
   */
  subscribeToDevice(deviceId: string): void {
    if (this.connected && this.socket) {
      const message = {
        type: MessageType.SUBSCRIBE,
        device_id: deviceId
      };
      this.socket.send(JSON.stringify(message));
    }
  }

  /**
   * Unsubscribe from updates for a specific device
   * @param deviceId Device ID to unsubscribe from
   */
  unsubscribeFromDevice(deviceId: string): void {
    if (this.connected && this.socket) {
      const message = {
        type: MessageType.UNSUBSCRIBE,
        device_id: deviceId
      };
      this.socket.send(JSON.stringify(message));
    }
  }

  /**
   * Send command to device
   * @param deviceId Target device ID
   * @param command Command name
   * @param params Command parameters
   */
  sendCommand(deviceId: string, command: string, params: any = {}): void {
    if (this.connected && this.socket) {
      const message = {
        type: MessageType.COMMAND,
        device_id: deviceId,
        command,
        params
      };
      this.socket.send(JSON.stringify(message));
    }
  }

  /**
   * Check if connected to WebSocket server
   */
  isConnected(): boolean {
    return this.connected;
  }
}
