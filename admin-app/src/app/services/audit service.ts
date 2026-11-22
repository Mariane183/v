import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface AuditLogItem {
  id: string;
  action: string;
  details: string;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuditService {
  private logsSubject = new BehaviorSubject<AuditLogItem[]>(this.loadLogsFromStorage());
  logs$ = this.logsSubject.asObservable();

  constructor() {}

  private loadLogsFromStorage(): AuditLogItem[] {
    const saved = localStorage.getItem('barangay_audit_logs');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return [];
      }
    }
    return [];
  }

  getLogs(): AuditLogItem[] {
    return this.logsSubject.getValue();
  }

 
  addLog(action: string, details: string) {
    const currentLogs = this.getLogs();
    const newLog: AuditLogItem = {
      id: Date.now().toString(),
      action: action,
      details: details,
      timestamp: new Date().toLocaleString() 
    };

    const updatedLogs = [newLog, ...currentLogs];
    this.logsSubject.next(updatedLogs);
    localStorage.setItem('barangay_audit_logs', JSON.stringify(updatedLogs));
  }
}