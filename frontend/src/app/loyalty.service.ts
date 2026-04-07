import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface HighRiskCustomer {
  customer_id: string;
  source: string;
  loyalty_tier: string;
  enrollment_date: string;
  weeks_since_enrollment: number;
  points_accrued: number;
  redeemed_total: number;
  zero_redemption_flag: boolean;
  last_redemption_date: string | null;
  risk_level: 'critical' | 'high' | 'medium';
  risk_score: number;
  // CRM
  account_status: string;
  segment: string;
  engagement_score: number | null;
  last_purchase_days_ago: number | null;
  crm_churn_flag: boolean | null;
  // Email
  email_open_rate_pct: number | null;
  emails_sent_90d: number | null;
  unsubscribed: boolean | null;
  // Shopify
  total_orders: number | null;
  total_spend: number | null;
  avg_order_value: number | null;
  last_order_date: string | null;
  // GA
  sessions_last_30d: number | null;
  session_drop_pct: number | null;
  browsing_intent_collapse: boolean | null;
  // Support
  unresolved_tickets: number | null;
  csat_score: number | null;
}

export interface PipelineResult {
  customers: HighRiskCustomer[];
  summary: string;
  orchestration_summary: string;
  agent_mode: 'claude' | 'direct';
  total_sources: number;
}

@Injectable({ providedIn: 'root' })
export class LoyaltyService {
  private http = inject(HttpClient);
  private baseUrl = 'http://localhost:8080';

  getHighRiskCustomers(): Observable<PipelineResult> {
    return this.http.get<PipelineResult>(`${this.baseUrl}/api/high-risk-customers`);
  }
}
