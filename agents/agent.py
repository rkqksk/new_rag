class FrontendAgent:
    def __init__(self, project_info):
        self.project_info = project_info

    def generate_component(self, name, props):
        """리액트 컴포넌트 코드 자동 생성"""
        props_str = ', '.join(props)
        code = f"""import React from 'react';

const {name} = ({{ {props_str} }}) => (
  <div>
    /* {name} 컴포넌트 구현 */
  </div>
);

export default {name};
"""
        return code

    def write_docs(self, component_name, props):
        """컴포넌트 문서 자동 생성"""
        doc = f"""
### {component_name}

| Prop | Type | Description |
|------|------|-------------|
"""
        for prop in props:
            doc += f"| {prop} | string | 설명 필요 |\n"
        return doc

    def generate_test(self, component_name):
        """테스트 코드 생성 예시 (Jest/RTL)"""
        return f"""
import {{ render }} from '@testing-library/react';
import {component_name} from './{component_name}';

test('renders {component_name}', () => {{
  render(<{component_name} />);
}});
"""

    def refactor_code(self, old_code):
        """코드 리팩토링 예시"""
        # 간단 예시: 'class ' → 'function ' 치환
        refactored_code = old_code.replace('class ', 'function ')
        return refactored_code

    def create_api_integration(self, endpoint, method='GET'):
        """API 호출 코드 자동 생성 예시"""
        return f"""
import axios from 'axios';

export const fetchData = async () => {{
  const response = await axios.{method.lower()}('{endpoint}');
  return response.data;
}};
"""

# 사용 예시
agent = FrontendAgent(project_info={'name': 'Sample Project'})
component_code = agent.generate_component('SampleButton', ['label', 'onClick'])
docs = agent.write_docs('SampleButton', ['label', 'onClick'])
test_code = agent.generate_test('SampleButton')
api_code = agent.create_api_integration('https://api.example.com/data')

print(component_code)
print(docs)
print(test_code)
print(api_code)
