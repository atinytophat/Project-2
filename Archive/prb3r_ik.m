function theta = prb3r_ik(Qx, Qy, tipSlope, gammas, elbowMode)

if abs(sum(gammas) - 1.0) > 1e-12
    error('Characteristic radius factors must sum to 1');
end


px = Qx - gammas(4) * cos(tipSlope) - gammas(1);
py = Qy - gammas(4) * sin(tipSlope);

cosTheta2 = (px^2 + py^2 - gammas(2)^2 - gammas(3)^2) ...
    / (2.0 * gammas(2) * gammas(3));

if cosTheta2 < -1.0 || cosTheta2 > 1.0
    error('Target point is outside the reachable set for the given tip slope.');
end

cosTheta2 = max(-1.0, min(1.0, cosTheta2));

if strcmpi(elbowMode, 'down')
    theta2 = acos(cosTheta2);
elseif strcmpi(elbowMode, 'up')
    theta2 = -acos(cosTheta2);
else
    error('elbowMode must be ''down'' or ''up''.');
end

denom = gammas(2)^2 + gammas(3)^2 + 2.0 * gammas(2) * gammas(3) * cos(theta2);

cosTheta1 = (px * (gammas(2) + gammas(3) * cos(theta2)) ...
    + py * gammas(3) * sin(theta2)) / denom;

sinTheta1 = (py * (gammas(2) + gammas(3) * cos(theta2)) ...
    - px * gammas(3) * sin(theta2)) / denom;

theta1 = atan2(sinTheta1, cosTheta1);
theta3 = tipSlope - theta1 - theta2;

theta = [theta1; theta2; theta3];
end
