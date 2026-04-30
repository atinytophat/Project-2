function [Qx, Qy, tipSlope] = prb3r_fk(theta, gammas)

if abs(sum(gammas) - 1.0) > 1e-12
    error('Characteristic radius factors must sum to 1');
end

theta1 = theta(1);
theta2 = theta(2);
theta3 = theta(3);

t12 = theta1 + theta2;
t123 = t12 + theta3;

Qx = gammas(1) + gammas(2) * cos(theta1) + gammas(3) * cos(t12) + gammas(4) * cos(t123);
Qy = gammas(2) * sin(theta1) + gammas(3) * sin(t12) + gammas(4) * sin(t123);

tipSlope = t123;
end




