from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class TwitterPlugin(WebPlugin):
    name = "twitter"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWW5CpIk3n8",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(proxies=proxy, headers=headers) as client:
                # Get flow token
                init = await client.post(
                    "https://api.twitter.com/1.1/onboarding/task.json",
                    json={"flow_name": "login"}
                )
                flow_token = init.json().get("flow_token")
                
                # Submit username
                user_resp = await client.post(
                    "https://api.twitter.com/1.1/onboarding/task.json",
                    json={
                        "flow_token": flow_token,
                        "subtask_inputs": [{
                            "subtask_id": "LoginEnterUserIdentifier",
                            "settings_list": {
                                "setting_responses": [{
                                    "key": "user_identifier",
                                    "response_data": {"text_data": {"result": username}}
                                }]
                            }
                        }]
                    }
                )
                flow_token = user_resp.json().get("flow_token")
                
                # Submit password
                pass_resp = await client.post(
                    "https://api.twitter.com/1.1/onboarding/task.json",
                    json={
                        "flow_token": flow_token,
                        "subtask_inputs": [{
                            "subtask_id": "LoginEnterPassword",
                            "enter_password": {
                                "password": password,
                                "link": "next_link"
                            }
                        }]
                    }
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                data = pass_resp.json()
                
                if "auth_token" in str(data):
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(
                            cookies=dict(client.cookies),
                            tokens={"flow_token": flow_token}
                        )
                    )
                
                if "LoginTwoFactorAuthChallenge" in str(data):
                    return LoginResult(
                        result=AuthResult.MFA_REQUIRED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                errors = data.get("errors", [])
                if errors:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message=errors[0].get("message", "Unknown error")
                    )
                
                return LoginResult(
                    result=AuthResult.UNKNOWN,
                    username=username,
                    password=password,
                    response_time_ms=elapsed
                )
                
        except Exception as e:
            return LoginResult(
                result=AuthResult.ERROR,
                username=username,
                password=password,
                message=str(e)
            )