"""
Serviços para o módulo de Recursos Humanos
Sistema completo de gestão de pessoas e folha de pagamento
"""

from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from app import db
from models import Employee, Department, Position, Attendance, Leave, Payroll, Performance


class HRService:
    """Serviço principal para gestão de RH"""
    
    # Tabelas de cálculo de impostos trabalhistas (Brasil)
    INSS_RATES = [
        {'min': 0, 'max': 1302.00, 'rate': 0.075},
        {'min': 1302.01, 'max': 2571.29, 'rate': 0.09},
        {'min': 2571.30, 'max': 3856.94, 'rate': 0.12},
        {'min': 3856.95, 'max': 7507.49, 'rate': 0.14},
        {'min': 7507.50, 'max': float('inf'), 'rate': 0, 'max_value': 876.97}
    ]
    
    IRRF_RATES = [
        {'min': 0, 'max': 1903.98, 'rate': 0, 'deduction': 0},
        {'min': 1903.99, 'max': 2826.65, 'rate': 0.075, 'deduction': 142.80},
        {'min': 2826.66, 'max': 3751.05, 'rate': 0.15, 'deduction': 354.80},
        {'min': 3751.06, 'max': 4664.68, 'rate': 0.225, 'deduction': 636.13},
        {'min': 4664.69, 'max': float('inf'), 'rate': 0.275, 'deduction': 869.36}
    ]
    
    def __init__(self):
        self.fgts_rate = 0.08  # 8% FGTS
        self.pis_rate = 0.0165  # 1.65% PIS sobre folha
    
    def calculate_inss(self, gross_salary: Decimal) -> Decimal:
        """Calcula desconto do INSS"""
        salary_float = float(gross_salary)
        
        for bracket in self.INSS_RATES:
            if bracket['min'] <= salary_float <= bracket['max']:
                if 'max_value' in bracket:
                    return Decimal(str(bracket['max_value']))
                else:
                    return gross_salary * Decimal(str(bracket['rate']))
        
        return Decimal('0')
    
    def calculate_irrf(self, gross_salary: Decimal, dependents: int = 0) -> Decimal:
        """Calcula desconto do IRRF"""
        # Dedução por dependente (R$ 189,59 por dependente em 2024)
        dependent_deduction = Decimal('189.59') * dependents
        
        # Base de cálculo (salário bruto - INSS - dependentes)
        inss = self.calculate_inss(gross_salary)
        taxable_income = gross_salary - inss - dependent_deduction
        
        if taxable_income <= 0:
            return Decimal('0')
        
        income_float = float(taxable_income)
        
        for bracket in self.IRRF_RATES:
            if bracket['min'] <= income_float <= bracket['max']:
                irrf = (taxable_income * Decimal(str(bracket['rate']))) - Decimal(str(bracket['deduction']))
                return max(irrf, Decimal('0'))
        
        return Decimal('0')
    
    def calculate_fgts(self, gross_salary: Decimal) -> Decimal:
        """Calcula FGTS (não é desconto, é depósito do empregador)"""
        return gross_salary * Decimal(str(self.fgts_rate))
    
    def calculate_payroll(self, employee_id: int, period_start: date, period_end: date, 
                         overtime_hours: Decimal = Decimal('0'), 
                         bonus: Decimal = Decimal('0'),
                         benefits: Dict = None) -> Dict:
        """
        Calcula folha de pagamento para um funcionário
        
        Args:
            employee_id: ID do funcionário
            period_start: Data início do período
            period_end: Data fim do período  
            overtime_hours: Horas extras trabalhadas
            bonus: Bônus/gratificação
            benefits: Dicionário com benefícios
            
        Returns:
            Dict com todos os cálculos da folha
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError(f"Funcionário {employee_id} não encontrado")
        
        if not benefits:
            benefits = {}
        
        # Cálculos base
        base_salary = employee.base_salary
        days_in_period = (period_end - period_start).days + 1
        working_days = self._calculate_working_days(period_start, period_end)
        
        # Salário proporcional
        salary_amount = base_salary
        
        # Horas extras
        hourly_rate = base_salary / Decimal('220')  # 220 horas/mês padrão
        overtime_rate = employee.overtime_rate or Decimal('1.5')
        overtime_amount = hourly_rate * overtime_rate * overtime_hours
        
        # Total de proventos
        gross_salary = salary_amount + overtime_amount + bonus
        
        # Benefícios
        meal_voucher = Decimal(str(benefits.get('meal_voucher', 0)))
        transport_voucher = Decimal(str(benefits.get('transport_voucher', 0)))
        family_allowance = Decimal(str(benefits.get('family_allowance', 0)))
        
        # Descontos obrigatórios
        inss_discount = self.calculate_inss(gross_salary)
        irrf_discount = self.calculate_irrf(gross_salary, benefits.get('dependents', 0))
        
        # Descontos opcionais
        health_insurance = Decimal(str(benefits.get('health_insurance', 0)))
        dental_insurance = Decimal(str(benefits.get('dental_insurance', 0)))
        meal_voucher_discount = meal_voucher * Decimal('0.2')  # 20% desconto padrão
        transport_voucher_discount = transport_voucher * Decimal('0.06')  # 6% desconto padrão
        
        # Total de descontos
        total_discounts = (inss_discount + irrf_discount + health_insurance + 
                          dental_insurance + meal_voucher_discount + transport_voucher_discount)
        
        # Salário líquido
        net_salary = gross_salary - total_discounts
        
        # FGTS (não é desconto do funcionário)
        fgts_amount = self.calculate_fgts(gross_salary)
        
        return {
            'employee_id': employee_id,
            'employee_name': employee.full_name,
            'period_start': period_start,
            'period_end': period_end,
            'working_days': working_days,
            
            # Base
            'base_salary': base_salary,
            'hours_worked': Decimal('220'),  # Padrão, pode ser ajustado
            'overtime_hours': overtime_hours,
            
            # Proventos
            'salary_amount': salary_amount,
            'overtime_amount': overtime_amount,
            'bonus_amount': bonus,
            'gross_salary': gross_salary,
            
            # Benefícios
            'meal_voucher': meal_voucher,
            'transport_voucher': transport_voucher,
            'family_allowance': family_allowance,
            'total_benefits': meal_voucher + transport_voucher + family_allowance,
            
            # Descontos
            'inss_discount': inss_discount,
            'irrf_discount': irrf_discount,
            'health_insurance': health_insurance,
            'dental_insurance': dental_insurance,
            'meal_voucher_discount': meal_voucher_discount,
            'transport_voucher_discount': transport_voucher_discount,
            'total_discounts': total_discounts,
            
            # Resultado final
            'net_salary': net_salary,
            'fgts_amount': fgts_amount,
            
            # Custos para empresa
            'employer_cost': gross_salary + fgts_amount + (gross_salary * Decimal('0.2')),  # Estimativa com encargos
            
            'calculation_date': datetime.now().isoformat()
        }
    
    def _calculate_working_days(self, start_date: date, end_date: date) -> int:
        """Calcula dias úteis no período"""
        current_date = start_date
        working_days = 0
        
        while current_date <= end_date:
            # Monday = 0, Sunday = 6
            if current_date.weekday() < 5:  # Não é sábado ou domingo
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def create_payroll_batch(self, period_start: date, period_end: date, 
                           department_id: Optional[int] = None) -> List[Dict]:
        """Cria folha de pagamento em lote para múltiplos funcionários"""
        
        query = Employee.query.filter(Employee.status == 'active')
        
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        
        employees = query.all()
        payroll_results = []
        
        for employee in employees:
            try:
                # Buscar dados específicos do funcionário (horas extras, benefícios, etc.)
                overtime_hours = self._get_employee_overtime(employee.id, period_start, period_end)
                benefits = self._get_employee_benefits(employee.id)
                
                payroll_calc = self.calculate_payroll(
                    employee.id, period_start, period_end, 
                    overtime_hours, Decimal('0'), benefits
                )
                
                payroll_results.append(payroll_calc)
                
            except Exception as e:
                payroll_results.append({
                    'employee_id': employee.id,
                    'employee_name': employee.full_name,
                    'error': str(e)
                })
        
        return payroll_results
    
    def _get_employee_overtime(self, employee_id: int, start_date: date, end_date: date) -> Decimal:
        """Busca horas extras do funcionário no período"""
        attendances = Attendance.query.filter(
            Attendance.employee_id == employee_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()
        
        total_overtime = Decimal('0')
        for attendance in attendances:
            if attendance.overtime_hours:
                total_overtime += attendance.overtime_hours
        
        return total_overtime
    
    def _get_employee_benefits(self, employee_id: int) -> Dict:
        """Busca benefícios do funcionário"""
        # Em uma implementação real, isso viria de uma tabela de benefícios
        # Por enquanto, retornamos valores padrão
        return {
            'meal_voucher': 500.00,
            'transport_voucher': 200.00,
            'family_allowance': 0.00,
            'health_insurance': 150.00,
            'dental_insurance': 50.00,
            'dependents': 0
        }
    
    def generate_performance_metrics(self, employee_id: int, period_months: int = 6) -> Dict:
        """Gera métricas de performance do funcionário"""
        
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError(f"Funcionário {employee_id} não encontrado")
        
        # Período de análise
        end_date = date.today()
        start_date = end_date - timedelta(days=period_months * 30)
        
        # Buscar avaliações
        evaluations = Performance.query.filter(
            Performance.employee_id == employee_id,
            Performance.evaluation_date >= start_date
        ).all()
        
        # Buscar faltas e atrasos
        attendances = Attendance.query.filter(
            Attendance.employee_id == employee_id,
            Attendance.date >= start_date
        ).all()
        
        # Calcular métricas
        total_days = len(attendances) if attendances else 0
        late_days = sum(1 for att in attendances if att.is_late) if attendances else 0
        absent_days = sum(1 for att in attendances if att.is_absent) if attendances else 0
        
        # Scores médios das avaliações
        avg_scores = {}
        if evaluations:
            scores = ['productivity_score', 'quality_score', 'teamwork_score', 
                     'communication_score', 'leadership_score', 'innovation_score', 'punctuality_score']
            
            for score in scores:
                values = [getattr(eval, score) for eval in evaluations if getattr(eval, score)]
                avg_scores[score] = sum(values) / len(values) if values else 0
        
        return {
            'employee_id': employee_id,
            'employee_name': employee.full_name,
            'department': employee.department.name if employee.department else 'N/A',
            'position': employee.position.title if employee.position else 'N/A',
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            
            # Métricas de assiduidade
            'attendance': {
                'total_days': total_days,
                'late_days': late_days,
                'absent_days': absent_days,
                'punctuality_rate': ((total_days - late_days) / total_days * 100) if total_days > 0 else 100,
                'attendance_rate': ((total_days - absent_days) / total_days * 100) if total_days > 0 else 100
            },
            
            # Avaliações de performance
            'performance_scores': avg_scores,
            'overall_performance': sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0,
            
            # Número de avaliações no período
            'evaluations_count': len(evaluations),
            
            # Tempo na empresa
            'years_of_service': (date.today() - employee.hire_date).days / 365.25 if employee.hire_date else 0,
            
            'generated_at': datetime.now().isoformat()
        }
    
    def calculate_vacation_days(self, employee_id: int) -> Dict:
        """Calcula saldo de férias do funcionário"""
        
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError(f"Funcionário {employee_id} não encontrado")
        
        hire_date = employee.hire_date
        today = date.today()
        
        # Calcular períodos aquisitivos completos
        years_worked = (today - hire_date).days / 365.25
        complete_periods = int(years_worked)
        
        # Dias de férias por período (30 dias por ano no Brasil)
        vacation_days_per_year = 30
        total_earned = complete_periods * vacation_days_per_year
        
        # Buscar férias já tiradas
        taken_leaves = Leave.query.filter(
            Leave.employee_id == employee_id,
            Leave.leave_type == 'vacation',
            Leave.status == 'approved'
        ).all()
        
        total_taken = sum(leave.days_approved or 0 for leave in taken_leaves)
        
        # Saldo atual
        current_balance = total_earned - total_taken
        
        # Próximo período aquisitivo
        next_acquisition = hire_date.replace(year=hire_date.year + complete_periods + 1)
        days_until_next = (next_acquisition - today).days
        
        return {
            'employee_id': employee_id,
            'employee_name': employee.full_name,
            'hire_date': hire_date.isoformat(),
            'years_worked': round(years_worked, 2),
            'complete_periods': complete_periods,
            'total_earned_days': total_earned,
            'total_taken_days': total_taken,
            'current_balance': current_balance,
            'next_acquisition_date': next_acquisition.isoformat(),
            'days_until_next_acquisition': max(days_until_next, 0),
            'vacation_history': [
                {
                    'start_date': leave.start_date.isoformat(),
                    'end_date': leave.end_date.isoformat(),
                    'days': leave.days_approved or leave.days_requested,
                    'status': leave.status
                } for leave in taken_leaves
            ],
            'calculated_at': datetime.now().isoformat()
        }


# Instância global do serviço
hr_service = HRService()


def calculate_employee_payroll(employee_id: int, period_start: date, period_end: date, **kwargs) -> Dict:
    """Função helper para cálculo de folha individual"""
    return hr_service.calculate_payroll(employee_id, period_start, period_end, **kwargs)


def get_employee_performance(employee_id: int, period_months: int = 6) -> Dict:
    """Função helper para métricas de performance"""
    return hr_service.generate_performance_metrics(employee_id, period_months)


def get_vacation_balance(employee_id: int) -> Dict:
    """Função helper para saldo de férias"""
    return hr_service.calculate_vacation_days(employee_id)