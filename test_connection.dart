import 'dart:io';
import 'dart:convert';

void main() async {
  print('🧪 正在测试前后端连接...');
  
  // 测试基本连接
  await testBasicConnection();
  
  // 测试API端点
  await testApiEndpoints();
  
  print('✅ 连接测试完成!');
}

Future<void> testBasicConnection() async {
  print('\n📡 测试基本连接...');
  
  try {
    final client = HttpClient();
    final request = await client.getUrl(Uri.parse('http://10.20.71.106:8000'));
    final response = await request.close();
    
    if (response.statusCode == 200) {
      print('✅ 后端服务连接成功 (状态码: ${response.statusCode})');
    } else {
      print('⚠️ 后端服务响应异常 (状态码: ${response.statusCode})');
    }
    
    client.close();
  } catch (e) {
    print('❌ 连接失败: $e');
  }
}

Future<void> testApiEndpoints() async {
  print('\n🔍 测试API端点...');
  
  final endpoints = [
    '/docs',
    '/api/auth',
    '/api/auth/register',
    '/api/foods/records',
  ];
  
  for (final endpoint in endpoints) {
    await testEndpoint(endpoint);
  }
}

Future<void> testEndpoint(String endpoint) async {
  try {
    final client = HttpClient();
    final url = 'http://10.20.71.106:8000$endpoint';
    final request = await client.getUrl(Uri.parse(url));
    final response = await request.close();
    
    print('  $endpoint -> 状态码: ${response.statusCode}');
    
    client.close();
  } catch (e) {
    print('  $endpoint -> 错误: $e');
  }
} 