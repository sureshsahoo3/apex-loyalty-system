import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LoyaltyService, HighRiskCustomer, PipelineResult } from './loyalty.service';

export interface ConfirmModal {
  riskLevel: string;
  customers: HighRiskCustomer[];
}

export interface GroupStats {
  avgWeeksEnrolled: number;
  avgPointsAccrued: number;
  avgLifetimeValue: number;
}

export interface Toast {
  id: number;
  riskLevel: string;
  count: number;
}

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  private loyaltyService = inject(LoyaltyService);

  loading  = signal(false);
  error    = signal<string | null>(null);
  result   = signal<PipelineResult | null>(null);
  modal    = signal<ConfirmModal | null>(null);
  toasts   = signal<Toast[]>([]);
  sentGroups = signal<Set<string>>(new Set());
  private toastId = 0;

  searchTerm = signal('');
  sortColumn = signal<keyof HighRiskCustomer>('weeks_since_enrollment');
  sortAsc    = signal(false);

  readonly riskGroups = ['critical', 'high', 'medium'] as const;

  readonly riskLabels: Record<string, string> = {
    critical: 'Critical',
    high:     'High',
    medium:   'Medium',
  };

  readonly riskColors: Record<string, string> = {
    critical: '#ef4444',
    high:     '#fb923c',
    medium:   '#facc15',
  };

  readonly riskMessages: Record<string, string> = {
    critical: 'These customers are at critical churn risk — immediate action required.',
    high:     'These customers show strong churn signals and need prompt outreach.',
    medium:   'These customers show early churn signals and would benefit from re-engagement.',
  };

  /** Customers filtered by search, grouped by risk level. */
  groupedCustomers = computed(() => {
    const customers = this.result()?.customers ?? [];
    const search = this.searchTerm().toLowerCase();

    const filtered = search
      ? customers.filter(c =>
          c.customer_id.toLowerCase().includes(search) ||
          (c.loyalty_tier ?? '').toLowerCase().includes(search) ||
          (c.segment ?? '').toLowerCase().includes(search))
      : customers;

    const groups: Record<string, HighRiskCustomer[]> = { critical: [], high: [], medium: [] };
    for (const c of filtered) {
      (groups[c.risk_level] ??= []).push(c);
    }
    // Sort each group
    const col = this.sortColumn();
    const asc = this.sortAsc();
    for (const key of Object.keys(groups)) {
      groups[key].sort((a, b) => {
        const va = (a as any)[col] ?? 0;
        const vb = (b as any)[col] ?? 0;
        return asc ? (va < vb ? -1 : 1) : (va > vb ? -1 : 1);
      });
    }
    return groups;
  });

  counts = computed(() => {
    const all = this.result()?.customers ?? [];
    return {
      total:    all.length,
      critical: all.filter(c => c.risk_level === 'critical').length,
      high:     all.filter(c => c.risk_level === 'high').length,
      medium:   all.filter(c => c.risk_level === 'medium').length,
    };
  });

  /** Derive which of the 4 README rules triggered for a customer. */
  riskSignals(c: HighRiskCustomer): { label: string; color: string }[] {
    const signals: { label: string; color: string }[] = [];
    if (c.redeemed_total === 0)
      signals.push({ label: 'Zero Redemptions', color: '#6366f1' });
    if ((c.unresolved_tickets ?? 0) >= 1)
      signals.push({ label: '2+ Tickets / Unresolved', color: '#f59e0b' });
    if ((c.session_drop_pct ?? 0) > 34)
      signals.push({ label: 'AOV Down 34%+', color: '#ef4444' });
    if (c.crm_churn_flag)
      signals.push({ label: '3/5 Orders Discounted', color: '#fb923c' });
    return signals;
  }

  ngOnInit() { this.loadData(); }

  loadData() {
    this.loading.set(true);
    this.error.set(null);
    this.loyaltyService.getHighRiskCustomers().subscribe({
      next: d  => { this.result.set(d); this.loading.set(false); },
      error: () => {
        this.error.set('Cannot reach backend on port 8080. Make sure the backend is running.');
        this.loading.set(false);
      }
    });
  }

  sortBy(col: keyof HighRiskCustomer) {
    this.sortColumn() === col
      ? this.sortAsc.update(v => !v)
      : (this.sortColumn.set(col), this.sortAsc.set(false));
  }

  sortIcon(col: string) {
    if (this.sortColumn() !== col) return '\u2195';
    return this.sortAsc() ? '\u2191' : '\u2193';
  }

  isGroupSent(riskLevel: string): boolean {
    return this.sentGroups().has(riskLevel);
  }

  campaignsSentCount = computed(() => this.sentGroups().size);

  /** Aggregate stats for the modal's customer group. */
  modalStats = computed<GroupStats | null>(() => {
    const customers = this.modal()?.customers;
    if (!customers?.length) return null;
    const avg = (fn: (c: HighRiskCustomer) => number) =>
      Math.round(customers.reduce((s, c) => s + (fn(c) ?? 0), 0) / customers.length);
    return {
      avgWeeksEnrolled: avg(c => c.weeks_since_enrollment),
      avgPointsAccrued: avg(c => c.points_accrued),
      avgLifetimeValue: avg(c => c.total_spend ?? 0),
    };
  });

  // ── Modal ──────────────────────────────────────────────────────────
  openModal(riskLevel: string) {
    const customers = this.groupedCustomers()[riskLevel] ?? [];
    if (!customers.length) return;
    this.modal.set({ riskLevel, customers });
  }

  closeModal() { this.modal.set(null); }

  confirmSend() {
    const m = this.modal();
    if (!m) return;

    this.sentGroups.update(s => new Set([...s, m.riskLevel]));

    const toast: Toast = { id: ++this.toastId, riskLevel: m.riskLevel, count: m.customers.length };
    this.toasts.update(t => [...t, toast]);
    setTimeout(() => this.toasts.update(t => t.filter(x => x.id !== toast.id)), 5000);

    this.closeModal();
  }

  dismissToast(id: number) {
    this.toasts.update(t => t.filter(x => x.id !== id));
  }
}
