"""
Manufacturing Expert Skill - 실제 사용 예제
사출성형 불량 분석 데모

이 예제는 다음을 보여줍니다:
1. manufacturing-expert skill 사용법
2. plugins/manufacturing_expert 직접 사용법
3. 사출성형 대표 불량 5가지 분석
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Method 1: Skill 사용 (Claude Code 방식)
from plugins.manufacturing_expert import ManufacturingExpertPlugin

# Method 2: Plugin 직접 사용 (Python 코드 방식)
plugin = ManufacturingExpertPlugin()


def analyze_injection_molding_defects():
    """사출성형 대표 불량 5가지 분석"""

    # 사출성형 대표 불량 문서
    defect_cases = [
        {
            "filename": "defect_flash_report.pdf",
            "content": """
            Defect Analysis Report - Flash

            Defect Type: Flash (burr, excess material)
            Product: Plastic housing component
            Material: ABS plastic
            Date: 2025-01-25

            Problem Description:
            Excess material found along parting line of molded parts.
            Flash thickness: 0.5mm - 1.2mm

            Root Cause Analysis:
            - Mold clamping force insufficient (current: 120 ton, required: 150 ton)
            - Mold wear detected on parting surface
            - Injection pressure too high (current: 180 MPa, spec: 150-160 MPa)

            Process Parameters:
            - Injection temperature: 220°C
            - Injection pressure: 180 MPa (HIGH)
            - Clamping force: 120 ton (LOW)
            - Cycle time: 45 seconds
            - PPM: 450 defects per million
            - Cpk: 0.89 (below target 1.33)

            Corrective Actions:
            1. Increase clamping force to 150 ton
            2. Reduce injection pressure to 155 MPa
            3. Schedule mold maintenance for parting surface repair
            4. Re-validate process with Cpk target > 1.33

            Standards: ISO 9001:2015, IATF 16949
            """
        },
        {
            "filename": "defect_short_shot_sop.pdf",
            "content": """
            Standard Operating Procedure - Short Shot Defect Investigation

            Defect: Short Shot (incomplete filling)
            Component: Automotive dashboard trim
            Material: PP+EPDM

            Symptoms:
            - Incomplete cavity filling
            - Missing features at flow end
            - Thin wall sections not formed

            Investigation Procedure:
            1. Check material flow rate (MFI test)
            2. Verify injection volume and pressure
            3. Inspect gate and runner system
            4. Check mold temperature distribution

            Typical Root Causes:
            - Insufficient injection pressure (< 140 MPa)
            - Low melt temperature (< 200°C for PP)
            - Gate size too small
            - Mold temperature too low
            - Material moisture content high

            Process Control:
            - Injection pressure: 160-180 MPa
            - Melt temperature: 210-230°C
            - Mold temperature: 40-60°C
            - Shot size: 95-98% of barrel capacity
            - Yield target: > 98%
            - OEE target: > 85%

            Quality Metrics:
            - Current PPM: 1200
            - Target PPM: < 100
            - Cpk: 0.67 (UNACCEPTABLE)

            Compliance: ISO 13485, FDA 21 CFR Part 820
            """
        },
        {
            "filename": "defect_sink_marks_fmea.pdf",
            "content": """
            FMEA Analysis - Sink Marks Defect

            Process: Injection Molding
            Part: Electronic enclosure
            Material: PC/ABS blend

            Defect Description:
            Surface depressions (sink marks) on thick sections due to volumetric
            shrinkage during cooling. Cosmetic defect affecting product appearance.

            Failure Mode: Visible sink marks on outer surface
            Severity: 7 (cosmetic defect, customer visible)
            Occurrence: 6 (frequent)
            Detection: 4 (visual inspection)
            RPN: 168 (HIGH RISK)

            Root Causes:
            - Non-uniform wall thickness (thick sections 6mm, thin 2mm)
            - Insufficient packing pressure
            - Premature gate freeze-off
            - Cooling time too short

            Current Process:
            - Packing pressure: 60 MPa (LOW)
            - Packing time: 8 seconds
            - Cooling time: 20 seconds (SHORT)
            - Wall thickness ratio: 3:1 (POOR DESIGN)

            Recommended Actions:
            1. Increase packing pressure to 80-90 MPa
            2. Extend packing time to 12-15 seconds
            3. Increase cooling time to 30 seconds
            4. Design change: reduce wall thickness variation to 1.5:1
            5. Add gas-assist or water-assist injection

            Quality Impact:
            - Defect rate: 15%
            - Scrap cost: $2,500/month
            - Customer complaints: 12/month
            - MTBF: 45 days between quality holds

            Standards: ISO 9001, GMP guidelines
            """
        },
        {
            "filename": "defect_warpage_control_plan.pdf",
            "content": """
            Control Plan - Warpage Prevention

            Part Name: Precision cover lens
            Material: PMMA (Acrylic)
            Process: Injection molding
            Critical Characteristic: Flatness (warpage < 0.2mm)

            Defect Type: Warpage (dimensional distortion)

            Problem Statement:
            Parts exhibit excessive warpage after ejection, causing assembly
            fit issues. Current warpage: 0.8-1.5mm (spec: < 0.2mm)

            Critical Process Parameters:

            Parameter          | Target    | Control Limit | Current
            -------------------|-----------|---------------|----------
            Melt temp          | 240°C     | ±5°C         | 245°C
            Mold temp          | 70°C      | ±3°C         | 65°C (LOW)
            Injection speed    | 80 mm/s   | ±10 mm/s     | 95 mm/s (HIGH)
            Cooling time       | 45 sec    | ±5 sec       | 35 sec (SHORT)
            Ejection temp      | 80°C      | ±5°C         | 95°C (HIGH)

            Quality Metrics:
            - Cp: 0.85 (INADEQUATE)
            - Cpk: 0.62 (UNACCEPTABLE)
            - Yield: 72% (TARGET: > 95%)
            - Defect rate: 28%

            Root Cause Analysis (5 Why):
            1. Why warpage? → Non-uniform cooling
            2. Why non-uniform? → Mold temperature imbalance
            3. Why imbalance? → Cooling channels blocked
            4. Why blocked? → Scale buildup in water lines
            5. Why buildup? → No preventive maintenance schedule

            Corrective Actions:
            1. Implement PM schedule for cooling system (monthly)
            2. Balance mold temperature to 70°C ±2°C
            3. Reduce injection speed to 80 mm/s
            4. Extend cooling time to 45 seconds
            5. Install conformal cooling channels

            Monitoring:
            - SPC charts for flatness measurement
            - Daily Cpk calculation (target > 1.33)
            - Weekly process capability review

            Standards: ISO 9001:2015, Six Sigma methodology
            """
        },
        {
            "filename": "defect_burn_marks_8d.pdf",
            "content": """
            8D Report - Burn Marks Defect

            Problem: Burn marks (discoloration) on molded parts
            Part: Consumer electronics housing
            Material: PC (Polycarbonate)
            Date Opened: 2025-01-20

            D1 - Team Formation:
            - Process Engineer
            - Quality Engineer
            - Production Supervisor
            - Tooling Technician

            D2 - Problem Description:
            Brown/black discoloration marks appearing on part surface near
            gate and thin-wall areas. Defect rate: 8% (unacceptable)

            D3 - Interim Containment:
            - 100% visual inspection implemented
            - Sorting of suspect inventory (2,500 units)
            - Customer notification sent

            D4 - Root Cause Analysis:
            Primary causes identified:
            1. Air trapping in cavity (gas combustion)
            2. Excessive injection speed (120 mm/s, spec: 60-80 mm/s)
            3. Insufficient venting at flow end
            4. Material degradation (residence time > 10 minutes)

            Process Data:
            - Injection speed: 120 mm/s (EXCESSIVE)
            - Barrel temperature: 310°C (spec: 280-300°C) - OVERHEATED
            - Screw RPM: 180 rpm (HIGH)
            - Residence time: 12 minutes (EXCESSIVE)
            - Back pressure: 15 MPa (HIGH)

            D5 - Permanent Corrective Actions:
            1. Reduce injection speed to 70 mm/s
            2. Lower barrel temp to 290°C
            3. Add venting slots (0.02mm depth) at 6 locations
            4. Reduce cycle time to keep residence < 8 minutes
            5. Optimize screw speed to 120 rpm

            D6 - Validation:
            - Trial run: 500 parts produced
            - Defect rate: 0.2% (ACCEPTABLE)
            - Cpk improved: 0.78 → 1.45
            - PPM: 8000 → 200

            D7 - Prevent Recurrence:
            - Update process parameters in SOP
            - Add burn mark check to operator training
            - Implement real-time barrel temperature monitoring
            - FMEA updated with new controls

            D8 - Congratulate Team:
            Cost savings: $15,000/month
            Quality improvement: 97.5% reduction in defects
            Customer satisfaction: No complaints in 2 weeks

            Quality Standards: ISO 9001, IATF 16949, Six Sigma
            Methodology: 8D, Root Cause Analysis, SPC
            """
        }
    ]

    print("=" * 80)
    print("🏭 Manufacturing Expert Skill - 사출성형 불량 분석 데모")
    print("=" * 80)
    print()

    results = []

    for i, defect_case in enumerate(defect_cases, 1):
        print(f"\n{'='*80}")
        print(f"📋 Case {i}: {defect_case['filename']}")
        print(f"{'='*80}")

        # Plugin을 사용하여 문서 분석
        result = plugin.process_document(defect_case)

        print(f"\n✅ 분석 결과:")
        print(f"   문서 타입: {result.metadata.doc_type}")
        print(f"   도메인: {result.metadata.domain}")
        print(f"   카테고리: {', '.join(result.metadata.categories)}")
        print(f"   성공: {result.success}")
        print(f"   청크 수: {len(result.chunks)}")

        # 추출된 용어 출력
        if result.metadata.terminology:
            print(f"\n🔍 추출된 제조 용어 ({len(result.metadata.terminology)}개):")
            for term in result.metadata.terminology[:10]:  # 처음 10개만
                print(f"   - {term}")
            if len(result.metadata.terminology) > 10:
                print(f"   ... 외 {len(result.metadata.terminology) - 10}개")

        results.append({
            'filename': defect_case['filename'],
            'result': result
        })

        print()

    return results


def demonstrate_dual_usage():
    """Plugin을 두 가지 방법으로 사용하는 예제"""

    test_doc = {
        "filename": "process_capability_study.pdf",
        "content": """
        Process Capability Study - Injection Molding

        Study Period: 2025-01-01 to 2025-01-15
        Sample Size: 500 parts

        Measurements:
        - Dimension A: Mean 50.02mm, Std Dev 0.15mm
        - USL: 50.5mm, LSL: 49.5mm
        - Cp: 1.11
        - Cpk: 1.08
        - PPM: 850
        - OEE: 78%
        - Yield: 91.5%

        Conclusion: Process capable but needs improvement.
        Target Cpk > 1.33 for production approval.

        Standards: ISO 9001:2015, SPC methodology
        """
    }

    print("\n" + "=" * 80)
    print("🔧 Plugin 사용 방법 비교")
    print("=" * 80)

    # Method 1: Plugin 직접 사용 (Python 코드에서)
    print("\n[Method 1] Plugin 직접 사용 (Python 코드):")
    print("-" * 80)
    plugin = ManufacturingExpertPlugin()
    result1 = plugin.process_document(test_doc)
    print(f"✅ 성공: {result1.metadata.doc_type}")
    print(f"   용어: {len(result1.metadata.terminology)}개 추출")

    # Method 2: Skill 경로를 통한 사용 (Claude Code에서)
    print("\n[Method 2] Skill 경로 사용 (Claude Code 방식):")
    print("-" * 80)
    sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'skills' / 'manufacturing-expert' / 'scripts'))
    import skill as manufacturing_skill
    result2 = manufacturing_skill.execute('process', test_doc)
    print(f"✅ 성공: {result2.metadata.doc_type}")
    print(f"   용어: {len(result2.metadata.terminology)}개 추출")

    # 두 결과가 동일함을 확인
    print("\n🔍 결과 비교:")
    print(f"   Method 1 doc_type: {result1.metadata.doc_type}")
    print(f"   Method 2 doc_type: {result2.metadata.doc_type}")
    print(f"   → 두 방법 모두 동일한 plugin 코드를 사용합니다!")


if __name__ == "__main__":
    # 사출성형 불량 분석 실행
    results = analyze_injection_molding_defects()

    print("\n" + "=" * 80)
    print("📊 전체 요약")
    print("=" * 80)
    print(f"총 분석 문서: {len(results)}건")
    print("\n불량 유형별:")
    for r in results:
        print(f"  - {r['filename']}: {r['result'].metadata.doc_type}")

    # 사용 방법 비교 데모
    demonstrate_dual_usage()

    print("\n" + "=" * 80)
    print("✅ 데모 완료!")
    print("=" * 80)
