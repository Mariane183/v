import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { AuditService } from '../services/audit service';

export interface CaseItem {
  id: string;
  caseNumber?: string;
  complainantName: string;
  respondentName: string;
  complaintType: string;
  status: string;
  blotterDetails?: string;
  hearingDate?: string;
  hearingHistory?: string[];
}

@Injectable({
  providedIn: 'root'
})
export class CaseService {
  private initialCases: CaseItem[] = [
    {
      id: '1',
      caseNumber: 'CASE-2026-001',
      complainantName: 'Juan Dela Cruz',
      respondentName: 'Pedro Santos',
      complaintType: 'Ingay at Alitan',
      status: 'Pending',
      blotterDetails: 'Nagreklamo dahil sa malakas na tunog tuwing gabi.',
      hearingDate: '2026-11-20',
      hearingHistory: ['Unang Patawag: 2026-11-10']
    }
  ];

  private casesSubject = new BehaviorSubject<CaseItem[]>(this.loadCasesFromStorage());
  cases$ = this.casesSubject.asObservable();

  constructor(private auditService: AuditService) {}

  private loadCasesFromStorage(): CaseItem[] {
    const saved = localStorage.getItem('barangay_cases');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return this.initialCases;
      }
    }
    return this.initialCases;
  }

  getCases(): CaseItem[] {
    return this.casesSubject.getValue();
  }

  getTotalCasesCount(): number {
    return this.getCases().length;
  }

  getCfaCount(): number {
    return this.getCases().filter(c => 
      c.status.toLowerCase().includes('cfa') || 
      c.status.toLowerCase().includes('ready for cfa')
    ).length;
  }

  updateCaseStatus(caseId: string | undefined, newStatus: string, blotterDetails?: string, hearingDate?: string) {
    if (!caseId) return;
    
    const currentCases = this.getCases();
    let targetCaseName = '';

    const updated = currentCases.map(c => {
      if (c.id === caseId || c.caseNumber === caseId) {
        targetCaseName = c.complainantName;
        return {
          ...c,
          status: newStatus,
          blotterDetails: blotterDetails !== undefined ? blotterDetails : c.blotterDetails,
          hearingDate: hearingDate !== undefined ? hearingDate : c.hearingDate
        };
      }
      return c;
    });

    this.casesSubject.next(updated);
    localStorage.setItem('barangay_cases', JSON.stringify(updated));

    this.auditService.addLog(
      'Case Update', 
      `Update status of  "${targetCaseName}" in: ${newStatus}`
    );
  }
}