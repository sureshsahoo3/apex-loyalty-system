import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LoyaltyService, HighRiskCustomer, PipelineResult } from './loyalty.service';

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  private loyaltyService = inject(LoyaltyService);

  loading = signal(false);
  error = signal<string | null>(null);
  result = signal<PipelineResult | null>(null);

  searchTerm = signal('');
  sortColumn = signal<keyof HighRiskCustomer>('weeks_since_enrollment');
  sortAsc = signal(false);
  filterTier = signal('All');
  filterRisk = signal('All');

  tiers = computed(() => {
    const tiers = new Set((this.result()?.customers ?? []).map(c => c.loyalty_tier));
    return ['All', ...Array.from(tiers).sort()];
  });

  counts = computed(() => {
    const all = this.result()?.customers ?? [];
    return {
      total: all.length,
      critical: all.filter(c => c.risk_level === 'critical').length,
      high:     all.filter(c => c.risk_level === 'high').length,
      medium:   all.filter(c => c.risk_level === 'medium').length,
    };
  });

  filteredCustomers = computed(() => {
    const customers = this.result()?.customers ?? [];
    const search = this.searchTerm().toLowerCase();
    const tier = this.filterTier();
    const risk = this.filterRisk();
    const col = this.sortColumn();
    const asc = this.sortAsc();

    let filtered = customers.filter(c => {
      const matchSearch = !search ||
        c.customer_id.toLowerCase().includes(search) ||
        c.loyalty_tier.toLowerCase().includes(search) ||
        (c.segment ?? '').toLowerCase().includes(search) ||
        (c.account_status ?? '').toLowerCase().includes(search);
      const matchTier = tier === 'All' || c.loyalty_tier === tier;
      const matchRisk = risk === 'All' || c.risk_level === risk.toLowerCase();
      return matchSearch && matchTier && matchRisk;
    });

    return [...filtered].sort((a, b) => {
      const va = (a as any)[col] ?? 0;
      const vb = (b as any)[col] ?? 0;
      if (va < vb) return asc ? -1 : 1;
      if (va > vb) return asc ? 1 : -1;
      return 0;
    });
  });

  ngOnInit() { this.loadData(); }

  loadData() {
    this.loading.set(true);
    this.error.set(null);
    this.loyaltyService.getHighRiskCustomers().subscribe({
      next: (data) => { this.result.set(data); this.loading.set(false); },
      error: () => {
        this.error.set('Cannot connect to backend on port 8080. Make sure the backend is running.');
        this.loading.set(false);
      }
    });
  }

  sortBy(col: keyof HighRiskCustomer) {
    if (this.sortColumn() === col) {
      this.sortAsc.update(v => !v);
    } else {
      this.sortColumn.set(col);
      this.sortAsc.set(false);
    }
  }

  sortIcon(col: string): string {
    if (this.sortColumn() !== col) return '\u2195';
    return this.sortAsc() ? '\u2191' : '\u2193';
  }
}
