#version 400

in vec3 texCoord;

out vec4 fragColor;

uniform sampler3D dataTex;
uniform sampler1D transFuncTex;
uniform sampler2D noiseTex;
uniform ivec2 noiseSize;
uniform vec3 viewerPos;
uniform vec3 lightPos;
uniform vec3 volMin;
uniform vec3 volMax;
uniform vec3 backColor;
uniform ivec2 viewportSize;

void composit(inout vec4 dst, in vec4 src)
{
	dst.rgb += (1.0 - dst.a) * src.a * src.rgb;
	dst.a += (1.0 - dst.a) * src.a;
}

float jitter(float jitterScale)
{
	vec2 noisePos = gl_FragCoord.xy / noiseSize;
	return texture2D(noiseTex, noisePos).r * jitterScale;
}

vec3 gradient(vec3 position)
{
	vec3 sample1, sample2;
	float delta = 0.01;
	sample1.x = texture(dataTex, position - vec3(delta, 0.0, 0.0)).r;
    sample2.x = texture(dataTex, position + vec3(delta, 0.0, 0.0)).r;
    sample1.y = texture(dataTex, position - vec3(0.0, delta, 0.0)).r;
    sample2.y = texture(dataTex, position + vec3(0.0, delta, 0.0)).r;
    sample1.z = texture(dataTex, position - vec3(0.0, 0.0, delta)).r;
    sample2.z = texture(dataTex, position + vec3(0.0, 0.0, delta)).r;
    return sample2 - sample1;
}

vec3 phongLighting(vec3 normalVec, vec3 lightVec, vec3 viewerVec, 
				vec3 ambientColor, vec3 diffuseColor, vec3 specularColor, float specExponent)
{
	float dist = length(lightVec);
	vec3 N = normalize(normalVec);
	vec3 L = normalize(lightVec);
	vec3 C = normalize(viewerVec);
	
	float constAttenuation = 0.2;
	float linearAttenuation = 0.5;
	float attenuation = 1.0 / (constAttenuation + linearAttenuation * dist);
	float nxDir = max(0.0, dot(N, L));
	diffuseColor *= nxDir * attenuation;
	
	vec3 halfVec = normalize(L + C);
	float nxHalf = max(0.0, dot(N, halfVec));
	float specPower = pow(nxHalf, specExponent);
	specularColor *= specPower * attenuation;
					
	return ambientColor + diffuseColor + specularColor;
}

bool insideVolume(vec3 position, vec3 volMin, vec3 volMax)
{
	vec3 temp1 = sign(position - volMin);
	vec3 temp2 = sign(volMax - position);
	float inside = dot(temp1, temp2);
	if(inside < 3.0) return false;
	return true;
}

void main()
{
	vec3 rayPos = texCoord;
	vec3 rayDir = normalize(rayPos - viewerPos);

	float jitterScale = 0.003;
	rayPos += jitter(jitterScale) * rayDir;	

	float referenceStepSize = 0.001; 
	float rayStepSize = 0.003;
	float alphaExp = rayStepSize / referenceStepSize;
	vec3 rayStep = rayDir * rayStepSize;
	vec4 dst = vec4(0.0);
	bool enableLighting = true;

	for(int i = 0; i < 1024; i++)
	{
		float dataSample = texture(dataTex, rayPos).r;

		vec4 src = texture(transFuncTex, dataSample);
		
		src.a = 1.0 - pow((1.0 - src.a), alphaExp); //opacity correction

		if (enableLighting && dataSample > 0.01)
		{
			vec3 N = gradient(rayPos);;
			vec3 L = rayPos - lightPos;
			vec3 V = rayPos - viewerPos;
			vec3 ambient = vec3(0.1);
			vec3 diffuse = vec3(0.6);
			vec3 specular = vec3(0.3);
			float specPower = 64;
			
			src.rgb *= phongLighting(N, L, V, ambient, diffuse, specular, specPower);
		}
		
		composit(dst, src);

		rayPos += rayStep;

		if (!insideVolume(rayPos, volMin, volMax)) 
			break;
	}

	fragColor = vec4(mix(backColor, dst.rgb, dst.a), 1.0);
}