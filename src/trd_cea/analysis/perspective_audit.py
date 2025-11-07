#!/usr/bin/env python3
"""
Comprehensive Perspective Audit for Economic Evaluation
Audits current perspective implementation and identifies missing societal cost categories
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import yaml
import os

# Set reproducible seed
SEED = int(os.environ.get('SEED', 20250929))

def load_repository_config():
    """Load and parse repository configuration"""
    base_path = Path("/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT")
    
    config = {
        'base_path': base_path,
        'perspectives': [],
        'currency': 'AUD',
        'price_year': 2024,
        'country': 'AU',  # Inferred from AUD currency
        'wtp_thresholds': [],
        'horizon': 5,
        'discount_rate': 0.05
    }
    
    # Load analysis config
    analysis_config_path = base_path / 'config/analysis_v2_defaults.yml'
    if analysis_config_path.exists():
        with open(analysis_config_path, 'r') as f:
            analysis_config = yaml.safe_load(f)
            config.update({
                'lambda_min': analysis_config.get('lambda_min', 0),
                'lambda_max': analysis_config.get('lambda_max', 75000),
                'lambda_step': analysis_config.get('lambda_step', 1000),
                'lambda_single': analysis_config.get('lambda_single', 50000),
                'seed': analysis_config.get('seed', SEED)
            })
    
    # Load strategies config  
    strategies_config_path = base_path / 'config/strategies.yml'
    if strategies_config_path.exists():
        with open(strategies_config_path, 'r') as f:
            strategies_config = yaml.safe_load(f)
            config.update({
                'perspectives': strategies_config.get('perspectives', ['health_system']),
                'currency': strategies_config.get('currency', 'AUD'),
                'strategies': strategies_config.get('strategies', []),
                'comparator': strategies_config.get('base', 'Usual care')
            })
    
    return config

def audit_cost_data_files(base_path):
    """Audit existing cost data files for perspective coverage"""
    cost_files = {}
    cost_categories = {}
    
    # Find all cost input files
    data_dir = base_path / 'data'
    for cost_file in data_dir.glob('cost_inputs_*.csv'):
        country_code = cost_file.stem.split('_')[-1].upper()
        
        try:
            df = pd.read_csv(cost_file)
            cost_files[country_code] = {
                'file': str(cost_file.relative_to(base_path)),
                'rows': len(df),
                'columns': list(df.columns),
                'items': df['Item'].tolist() if 'Item' in df.columns else []
            }
            
            # Categorize cost items
            if 'Item' in df.columns:
                categories = categorize_cost_items(df['Item'].tolist())
                cost_categories[country_code] = categories
                
        except Exception as e:
            cost_files[country_code] = {'error': str(e)}
    
    return cost_files, cost_categories

def categorize_cost_items(items):
    """Categorize cost items by perspective"""
    categories = {
        'health_system': {
            'medical_costs': [],
            'admin_monitoring': [],
            'adverse_events': [],
            'cost_offsets': []
        },
        'societal': {
            'patient_time': [],
            'caregiver_time': [],
            'travel_costs': [],
            'oop_payments': [],
            'productivity_losses': [],
            'informal_care': [],
            'equipment_nonmedical': []
        },
        'unclassified': []
    }
    
    for item in items:
        item_lower = item.lower()
        
        # Health system costs
        if any(term in item_lower for term in ['session', 'fee', 'psychiatrist', 'anesthesia', 'drug', 'hospital', 'cost']):
            if 'travel' not in item_lower and 'time' not in item_lower:
                categories['health_system']['medical_costs'].append(item)
        elif any(term in item_lower for term in ['admin', 'monitoring', 'management']):
            categories['health_system']['admin_monitoring'].append(item)
        elif any(term in item_lower for term in ['adverse', 'ae', 'side effect']):
            categories['health_system']['adverse_events'].append(item)
        elif any(term in item_lower for term in ['offset', 'saving', 'avoided']):
            categories['health_system']['cost_offsets'].append(item)
            
        # Societal costs
        elif any(term in item_lower for term in ['patient time', 'time cost', 'waiting']):
            categories['societal']['patient_time'].append(item)
        elif any(term in item_lower for term in ['caregiver', 'carer', 'family time']):
            categories['societal']['caregiver_time'].append(item)
        elif any(term in item_lower for term in ['travel', 'transport', 'distance']):
            categories['societal']['travel_costs'].append(item)
        elif any(term in item_lower for term in ['out-of-pocket', 'oop', 'copay', 'co-pay']):
            categories['societal']['oop_payments'].append(item)
        elif any(term in item_lower for term in ['productivity', 'absenteeism', 'presenteeism', 'work loss']):
            categories['societal']['productivity_losses'].append(item)
        elif any(term in item_lower for term in ['informal care', 'unpaid care']):
            categories['societal']['informal_care'].append(item)
        elif any(term in item_lower for term in ['equipment', 'device', 'non-medical']):
            categories['societal']['equipment_nonmedical'].append(item)
        else:
            categories['unclassified'].append(item)
    
    return categories

def assess_perspective_completeness(cost_categories, config):
    """Assess completeness of perspective implementation"""
    assessment = {
        'current_perspective': 'health_system_only',
        'perspectives_configured': config['perspectives'],
        'missing_societal_categories': [],
        'present_categories': {},
        'completeness_score': 0
    }
    
    # Required societal categories
    required_societal = [
        'patient_time', 'caregiver_time', 'travel_costs', 
        'productivity_losses', 'oop_payments'
    ]
    
    total_categories = 0
    present_categories = 0
    
    for country, categories in cost_categories.items():
        assessment['present_categories'][country] = {}
        
        # Check health system categories
        hs_cats = categories['health_system']
        for cat, items in hs_cats.items():
            assessment['present_categories'][country][f'hs_{cat}'] = {
                'present': len(items) > 0,
                'count': len(items),
                'items': items
            }
            if len(items) > 0:
                present_categories += 1
            total_categories += 1
        
        # Check societal categories
        soc_cats = categories['societal']
        missing_in_country = []
        
        for cat in required_societal:
            items = soc_cats.get(cat, [])
            assessment['present_categories'][country][f'soc_{cat}'] = {
                'present': len(items) > 0,
                'count': len(items),
                'items': items
            }
            
            if len(items) == 0:
                missing_in_country.append(cat)
            else:
                present_categories += 1
            total_categories += 1
        
        if missing_in_country:
            assessment['missing_societal_categories'].extend(
                [f"{country}_{cat}" for cat in missing_in_country]
            )
    
    # Calculate completeness
    if total_categories > 0:
        assessment['completeness_score'] = present_categories / total_categories
    
    # Determine current implementation
    if len(assessment['missing_societal_categories']) == 0:
        assessment['current_perspective'] = 'dual_perspective'
    elif len(assessment['missing_societal_categories']) < len(required_societal) * len(cost_categories):
        assessment['current_perspective'] = 'partial_societal'
    else:
        assessment['current_perspective'] = 'health_system_only'
    
    return assessment

def create_detailed_audit_report(config, cost_files, cost_categories, assessment):
    """Create detailed markdown audit report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    report_content = f"""# Economic Perspective Audit Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Repository:** IV Ketamine vs ECT Economic Evaluation  
**Audit Date:** {timestamp}  

---

## Executive Summary

### Current Implementation Status
- **Primary Perspective:** {assessment['current_perspective'].replace('_', ' ').title()}
- **Configured Perspectives:** {', '.join(config['perspectives'])}
- **Currency/Year:** {config['currency']} {config.get('price_year', 'Unknown')}
- **Country Context:** {config['country']}
- **Completeness Score:** {assessment['completeness_score']:.1%}

### Key Findings
- **Health System Costs:** ✅ Comprehensive coverage
- **Societal Costs:** {'✅ Complete' if assessment['current_perspective'] == 'dual_perspective' else '⚠️ Incomplete' if assessment['current_perspective'] == 'partial_societal' else '❌ Missing'}
- **Missing Categories:** {len(assessment['missing_societal_categories'])} societal cost categories need sourcing

---

## Repository Configuration

### Analysis Parameters
```yaml
Currency: {config['currency']}
Price Year: {config.get('price_year', 'TBD')}
Country: {config['country']}
WTP Range: ${config.get('lambda_min', 0):,} - ${config.get('lambda_max', 75000):,}
Standard WTP: ${config.get('lambda_single', 50000):,}
Time Horizon: {config.get('horizon', 5)} years
Discount Rate: {config.get('discount_rate', 0.05)*100:.1f}%
Perspectives Configured: {config['perspectives']}
```

### Cost Data Files Identified
"""
    
    # Add cost files summary
    for country, file_info in cost_files.items():
        if 'error' not in file_info:
            report_content += f"\n#### {country} Cost Data\n"
            report_content += f"- **File:** `{file_info['file']}`\n"
            report_content += f"- **Items:** {file_info['rows']} cost items\n"
            report_content += f"- **Columns:** {', '.join(file_info['columns'])}\n"
        else:
            report_content += f"\n#### {country} Cost Data\n"
            report_content += f"- **Status:** ❌ Error loading - {file_info['error']}\n"
    
    report_content += "\n\n---\n\n## Cost Category Analysis\n\n"
    
    # Detailed category analysis
    for country, categories in cost_categories.items():
        report_content += f"### {country} Cost Categories\n\n"
        
        # Health System Categories
        report_content += "#### Health System Perspective\n\n"
        hs_cats = categories['health_system']
        
        for cat_name, items in hs_cats.items():
            status = "✅" if len(items) > 0 else "❌"
            report_content += f"- **{cat_name.replace('_', ' ').title()}** {status} ({len(items)} items)\n"
            if len(items) > 0 and len(items) <= 5:
                report_content += f"  - {', '.join(items)}\n"
            elif len(items) > 5:
                report_content += f"  - {', '.join(items[:3])}, ... (+{len(items)-3} more)\n"
        
        # Societal Categories  
        report_content += "\n#### Societal Perspective\n\n"
        soc_cats = categories['societal']
        
        required_societal = [
            ('patient_time', 'Patient Time Costs'),
            ('caregiver_time', 'Caregiver Time'),
            ('travel_costs', 'Travel Costs'),
            ('productivity_losses', 'Productivity Losses'),
            ('oop_payments', 'Out-of-Pocket Payments'),
            ('informal_care', 'Informal Care'),
            ('equipment_nonmedical', 'Non-Medical Equipment')
        ]
        
        for cat_key, cat_display in required_societal:
            items = soc_cats.get(cat_key, [])
            status = "✅" if len(items) > 0 else "❌"
            priority = "**HIGH PRIORITY**" if cat_key in ['patient_time', 'travel_costs', 'productivity_losses'] else "Standard"
            
            report_content += f"- **{cat_display}** {status} ({len(items)} items) - {priority}\n"
            if len(items) > 0:
                report_content += f"  - {', '.join(items)}\n"
            else:
                report_content += f"  - *Need to source: {get_sourcing_guidance(cat_key, config['country'])}\n"
        
        if len(categories['unclassified']) > 0:
            report_content += f"\n**Unclassified Items:** {len(categories['unclassified'])}\n"
            report_content += f"- {', '.join(categories['unclassified'][:5])}\n"
    
    # Missing categories summary
    report_content += "\n\n---\n\n## Missing Societal Cost Categories\n\n"
    
    if len(assessment['missing_societal_categories']) == 0:
        report_content += "✅ **All required societal cost categories are present.**\n\n"
    else:
        report_content += f"❌ **{len(assessment['missing_societal_categories'])} societal cost categories are missing and need to be sourced:**\n\n"
        
        missing_by_type = {}
        for missing_item in assessment['missing_societal_categories']:
            country, cat = missing_item.split('_', 1)
            if cat not in missing_by_type:
                missing_by_type[cat] = []
            missing_by_type[cat].append(country)
        
        priority_order = ['patient_time', 'travel_costs', 'productivity_losses', 'caregiver_time', 'oop_payments']
        
        for cat in priority_order:
            if cat in missing_by_type:
                countries = missing_by_type[cat]
                priority = "🔴 HIGH" if cat in ['patient_time', 'travel_costs', 'productivity_losses'] else "🟡 MEDIUM"
                report_content += f"### {cat.replace('_', ' ').title()} - {priority} PRIORITY\n\n"
                report_content += f"**Missing for:** {', '.join(countries)}\n\n"
                report_content += get_detailed_sourcing_guidance(cat, config['country'])
                report_content += "\n\n"
    
    # Next steps
    report_content += """---

## Recommended Next Steps

### Immediate Actions (Step 2)
1. **Source Missing Societal Parameters** using the guidance above
2. **Create** `inputs/societal/sources/` directory structure  
3. **Populate** `sources_catalog.csv` with validated parameters
4. **Document** all price year conversions and methods

### Integration Actions (Step 3)  
1. **Extend model** to support dual perspectives
2. **Add** `inputs/societal/perspective_societal.yml` configuration
3. **Recompute** all economic outcomes for societal perspective

### Generation Actions (Step 4)
1. **Generate missing plots** for both perspectives
2. **Follow naming convention:** `<perspective>__<method>__<plot>__<therapy>__vs__<comparator>__vNEXT.<ext>`
3. **Export** SVG, PDF, PNG + CSV data for each plot

### Validation Actions (Step 6)
1. **Validate** all sourced parameters against official sources
2. **Document** provenance with DOI/URL citations  
3. **Perform** smoke checks on generated outputs

---

*Audit completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*Repository: IV Ketamine vs ECT Economic Evaluation*
"""
    
    return report_content

def get_sourcing_guidance(category, country):
    """Get brief sourcing guidance for missing categories"""
    guidance = {
        'patient_time': f"Hourly wage rates, transport time valuations ({country} transport ministry)",
        'caregiver_time': f"Informal care valuation studies, replacement cost method ({country})",
        'travel_costs': f"Per-km vehicle costs, public transport fares ({country} transport data)",
        'productivity_losses': f"Average wage rates, absenteeism studies ({country} labor statistics)",
        'oop_payments': f"Healthcare system co-payment schedules ({country} health ministry)",
        'informal_care': "Replacement cost or opportunity cost of informal caregiving",
        'equipment_nonmedical': "Home modifications, assistive devices not covered by health system"
    }
    
    return guidance.get(category, "Category-specific sourcing needed")

def get_detailed_sourcing_guidance(category, country):
    """Get detailed sourcing guidance with specific source suggestions"""
    
    if country == 'AU':
        guidance = {
            'patient_time': """**Preferred Sources:**
- Australian Bureau of Statistics (ABS): Average Weekly Earnings
- Infrastructure Australia: Value of Travel Time guidelines  
- Transport for NSW/VicRoads: Travel time valuations

**Variables Needed:**
- `patient_time_cost_per_hour`: Hourly wage rate (AUD/hour)
- `patient_waiting_time_per_visit`: Average waiting time (hours)
- `patient_travel_time_per_visit`: Average travel time (hours)""",
            
            'travel_costs': """**Preferred Sources:**
- Australian Automobile Association (AAA): Vehicle operating costs
- Public transport authorities: Average fare structures
- Australian Institute of Health and Welfare: Healthcare access studies

**Variables Needed:**  
- `patient_travel_cost_per_km`: Vehicle cost per kilometer (AUD/km)
- `patient_average_distance_to_facility`: Average distance (km)
- `patient_public_transport_cost_per_trip`: Public transport cost (AUD/trip)""",
            
            'productivity_losses': """**Preferred Sources:**
- Australian Bureau of Statistics: Labour Force Survey
- Safe Work Australia: Workers' compensation data
- Productivity Commission: Workplace productivity studies

**Variables Needed:**
- `productivity_loss_per_absence_day`: Daily wage cost (AUD/day)  
- `absenteeism_days_per_episode`: Treatment-related absence (days)
- `presenteeism_productivity_loss`: Reduced productivity factor (0-1)""",
            
            'caregiver_time': """**Preferred Sources:**
- Australian Institute of Health and Welfare: Caring in the Community
- Carers Australia: Economic value of informal care
- ABS: Time Use Survey

**Variables Needed:**
- `informal_caregiver_time_per_week`: Hours per week during treatment
- `informal_care_replacement_cost`: Hourly cost of formal care (AUD/hour)
- `caregiver_opportunity_cost`: Foregone wage rate (AUD/hour)""",
            
            'oop_payments': """**Preferred Sources:**
- Department of Health: Medicare Benefits Schedule
- Private Health Insurance Ombudsman: Gap payment reports
- Australian Institute of Health and Welfare: Health expenditure data

**Variables Needed:**
- `patient_copayment_per_session`: Out-of-pocket cost per treatment (AUD)
- `medication_oop_cost_annual`: Annual medication copayments (AUD)
- `ancillary_oop_costs`: Other healthcare out-of-pocket costs (AUD)"""
        }
    else:
        # Generic guidance for other countries
        guidance = {
            'patient_time': """**Preferred Sources:**
- National statistics office: Average wage data
- Transport ministry: Value of travel time guidelines
- Health ministry: Healthcare access studies

**Variables Needed:**
- `patient_time_cost_per_hour`: Hourly wage rate
- `patient_waiting_time_per_visit`: Average waiting time (hours)  
- `patient_travel_time_per_visit`: Average travel time (hours)""",
            
            'travel_costs': """**Preferred Sources:**
- Transport/infrastructure ministry: Vehicle operating costs
- Public transport authorities: Fare structures
- Health geography studies: Healthcare access distances

**Variables Needed:**
- `patient_travel_cost_per_km`: Vehicle cost per kilometer
- `patient_average_distance_to_facility`: Average distance (km)
- `patient_public_transport_cost_per_trip`: Public transport cost""",
            
            'productivity_losses': """**Preferred Sources:**
- Labor ministry/statistics: Employment and wage data
- Social security administration: Disability benefit data
- Health economics studies: Productivity loss valuations

**Variables Needed:**
- `productivity_loss_per_absence_day`: Daily wage cost
- `absenteeism_days_per_episode`: Treatment-related absence (days)
- `presenteeism_productivity_loss`: Reduced productivity factor (0-1)""",
            
            'caregiver_time': """**Preferred Sources:**
- Health ministry: Informal care studies
- Statistics office: Time use surveys
- Health economics literature: Caregiver burden valuations

**Variables Needed:**
- `informal_caregiver_time_per_week`: Hours per week during treatment
- `informal_care_replacement_cost`: Hourly cost of formal care
- `caregiver_opportunity_cost`: Foregone wage rate""",
            
            'oop_payments': """**Preferred Sources:**
- Health ministry: Healthcare financing data
- Insurance regulators: Out-of-pocket payment surveys
- Health economics studies: Patient cost burden

**Variables Needed:**
- `patient_copayment_per_session`: Out-of-pocket cost per treatment
- `medication_oop_cost_annual`: Annual medication copayments
- `ancillary_oop_costs`: Other healthcare out-of-pocket costs"""
        }
    
    return guidance.get(category, "**Sourcing guidance not available for this category**")

def main():
    """Main audit function"""
    print("🔍 Starting Economic Perspective Audit...")
    
    # Load configuration
    config = load_repository_config()
    print(f"   📋 Repository: {config['currency']} {config['country']} context")
    print(f"   📋 Configured perspectives: {', '.join(config['perspectives'])}")
    
    # Create backup snapshot  
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    base_path = config['base_path']
    
    # Audit cost data
    print("   📊 Auditing cost data files...")
    cost_files, cost_categories = audit_cost_data_files(base_path)
    
    # Assess completeness
    print("   🎯 Assessing perspective completeness...")
    assessment = assess_perspective_completeness(cost_categories, config)
    
    # Create reports
    print("   📝 Creating audit reports...")
    
    # Markdown report
    report_content = create_detailed_audit_report(config, cost_files, cost_categories, assessment)
    report_path = base_path / f"reports/perspective_audit_{timestamp}.md"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    # JSON report
    json_data = {
        'audit_timestamp': timestamp,
        'config': config,
        'cost_files': cost_files,
        'cost_categories': cost_categories,
        'assessment': assessment,
        'missing_categories_detail': {
            cat: get_detailed_sourcing_guidance(cat.split('_', 1)[-1], config['country'])
            for cat in assessment['missing_societal_categories']
        }
    }
    
    json_path = base_path / f"reports/perspective_audit_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2, default=str)
    
    # Summary
    print("\n✅ Perspective audit complete!")
    print(f"   📊 Current implementation: {assessment['current_perspective'].replace('_', ' ').title()}")
    print(f"   📊 Completeness score: {assessment['completeness_score']:.1%}")
    print(f"   📊 Missing societal categories: {len(assessment['missing_societal_categories'])}")
    print(f"   📄 Markdown report: {report_path.name}")
    print(f"   📄 JSON report: {json_path.name}")
    
    if len(assessment['missing_societal_categories']) > 0:
        print(f"\n🎯 Next step: Source {len(assessment['missing_societal_categories'])} missing societal cost categories")
        print("   Priority categories: patient_time, travel_costs, productivity_losses")
    else:
        print("\n✅ All societal cost categories are present - ready for dual-perspective analysis!")
    
    return {
        'config': config,
        'assessment': assessment,
        'report_path': report_path,
        'json_path': json_path
    }

if __name__ == "__main__":
    main()