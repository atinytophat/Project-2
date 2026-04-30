% Section 4 PRB 3R model from Haijun Su's paper.

clear;
clc;

mode = 'ik';

gammas = [0.10; 0.35; 0.40; 0.15];
kbar = [3.51; 2.99; 2.58];

Qx = 0.8;
Qy = 0.2;
tipSlope = 0.5;
lambda = 0.0;
phi = pi / 2.0;
eta = 0.0;
elbowMode = 'down';

if abs(sum(gammas) - 1.0) > 1e-12
    error('Characteristic radius factors must sum to 1.');
end

if strcmpi(mode, 'reference')
    fprintf('Section 4 reference stiffness values\n');
    fprintf('Eq. (24) gammas = [%.2f %.2f %.2f %.2f]\n', gammas(1), gammas(2), gammas(3), gammas(4));
    fprintf('Eq. (25) pure-moment kbar = [3.51933 2.78518 2.79756]\n');
    fprintf('Eq. (27) pure-force  kbar = [3.71591 2.87128 2.26417]\n');
    fprintf('Table 1 averaged kbar = [%.2f %.2f %.2f]\n', kbar(1), kbar(2), kbar(3));

elseif strcmpi(mode, 'ik')
    px = Qx - gammas(4) * cos(tipSlope) - gammas(1);
    py = Qy - gammas(4) * sin(tipSlope);

    cosTheta2 = (px^2 + py^2 - gammas(2)^2 - gammas(3)^2) / (2.0 * gammas(2) * gammas(3));
    cosTheta2 = max(-1.0, min(1.0, cosTheta2));

    if strcmpi(elbowMode, 'down')
        signValue = 1.0;
    else
        signValue = -1.0;
    end

    theta2 = signValue * acos(cosTheta2);
    denom = gammas(2)^2 + gammas(3)^2 + 2.0 * gammas(2) * gammas(3) * cos(theta2);
    cosTheta1 = (px * (gammas(2) + gammas(3) * cos(theta2)) + py * gammas(3) * sin(theta2)) / denom;
    sinTheta1 = (py * (gammas(2) + gammas(3) * cos(theta2)) - px * gammas(3) * sin(theta2)) / denom;
    theta1 = atan2(sinTheta1, cosTheta1);
    theta3 = tipSlope - theta1 - theta2;
    theta = [theta1; theta2; theta3];

    t12 = theta1 + theta2;
    t123 = t12 + theta3;
    QxOut = gammas(1) + gammas(2) * cos(theta1) + gammas(3) * cos(t12) + gammas(4) * cos(t123);
    QyOut = gammas(2) * sin(theta1) + gammas(3) * sin(t12) + gammas(4) * sin(t123);

    fprintf('Section 4.1 inverse kinematics\n');
    fprintf('theta = [%.6f %.6f %.6f]\n', theta(1), theta(2), theta(3));
    fprintf('reconstructed Q = [%.6f %.6f], tip slope = %.6f\n', QxOut, QyOut, t123);

elseif strcmpi(mode, 'stiffness')
    px = Qx - gammas(4) * cos(tipSlope) - gammas(1);
    py = Qy - gammas(4) * sin(tipSlope);

    cosTheta2 = (px^2 + py^2 - gammas(2)^2 - gammas(3)^2) / (2.0 * gammas(2) * gammas(3));
    cosTheta2 = max(-1.0, min(1.0, cosTheta2));

    if strcmpi(elbowMode, 'down')
        signValue = 1.0;
    else
        signValue = -1.0;
    end

    theta2 = signValue * acos(cosTheta2);
    denom = gammas(2)^2 + gammas(3)^2 + 2.0 * gammas(2) * gammas(3) * cos(theta2);
    cosTheta1 = (px * (gammas(2) + gammas(3) * cos(theta2)) + py * gammas(3) * sin(theta2)) / denom;
    sinTheta1 = (py * (gammas(2) + gammas(3) * cos(theta2)) - px * gammas(3) * sin(theta2)) / denom;
    theta1 = atan2(sinTheta1, cosTheta1);
    theta3 = tipSlope - theta1 - theta2;
    theta = [theta1; theta2; theta3];

    t12 = theta1 + theta2;
    t123 = t12 + theta3;
    J = [
        -(gammas(2) * sin(theta1) + gammas(3) * sin(t12) + gammas(4) * sin(t123)), ...
        -(gammas(3) * sin(t12) + gammas(4) * sin(t123)), ...
        -gammas(4) * sin(t123);
         gammas(2) * cos(theta1) + gammas(3) * cos(t12) + gammas(4) * cos(t123), ...
         gammas(3) * cos(t12) + gammas(4) * cos(t123), ...
         gammas(4) * cos(t123);
         1.0, 1.0, 1.0
    ];

    loadVec = [2.0 * lambda * cos(phi); 2.0 * lambda * sin(phi); eta];
    torque = J' * loadVec;
    kbarEq = torque ./ theta;

    fprintf('Section 4.3 equivalent stiffness from one beam state\n');
    fprintf('theta = [%.6f %.6f %.6f]\n', theta(1), theta(2), theta(3));
    fprintf('kbar = [%.6f %.6f %.6f]\n', kbarEq(1), kbarEq(2), kbarEq(3));
    fprintf('torque = [%.6f %.6f %.6f]\n', torque(1), torque(2), torque(3));

else
    theta = zeros(3, 1);

    for iter = 1:50
        t1 = theta(1);
        t2 = theta(2);
        t3 = theta(3);
        t12 = t1 + t2;
        t123 = t12 + t3;

        J = [
            -(gammas(2) * sin(t1) + gammas(3) * sin(t12) + gammas(4) * sin(t123)), ...
            -(gammas(3) * sin(t12) + gammas(4) * sin(t123)), ...
            -gammas(4) * sin(t123);
             gammas(2) * cos(t1) + gammas(3) * cos(t12) + gammas(4) * cos(t123), ...
             gammas(3) * cos(t12) + gammas(4) * cos(t123), ...
             gammas(4) * cos(t123);
             1.0, 1.0, 1.0
        ];

        loadVec = [2.0 * lambda * cos(phi); 2.0 * lambda * sin(phi); eta];
        residual = kbar .* theta - J' * loadVec;

        if norm(residual, 2) < 1e-10
            break;
        end

        h = 1e-8;
        tangent = zeros(3, 3);
        for c = 1:3
            shifted = theta;
            shifted(c) = shifted(c) + h;

            s1 = shifted(1);
            s2 = shifted(2);
            s3 = shifted(3);
            s12 = s1 + s2;
            s123 = s12 + s3;

            Jshift = [
                -(gammas(2) * sin(s1) + gammas(3) * sin(s12) + gammas(4) * sin(s123)), ...
                -(gammas(3) * sin(s12) + gammas(4) * sin(s123)), ...
                -gammas(4) * sin(s123);
                 gammas(2) * cos(s1) + gammas(3) * cos(s12) + gammas(4) * cos(s123), ...
                 gammas(3) * cos(s12) + gammas(4) * cos(s123), ...
                 gammas(4) * cos(s123);
                 1.0, 1.0, 1.0
            ];

            residualShift = kbar .* shifted - Jshift' * loadVec;
            tangent(:, c) = (residualShift - residual) / h;
        end

        delta = -tangent \ residual;
        theta = theta + delta;
    end

    t1 = theta(1);
    t2 = theta(2);
    t3 = theta(3);
    t12 = t1 + t2;
    t123 = t12 + t3;
    QxOut = gammas(1) + gammas(2) * cos(t1) + gammas(3) * cos(t12) + gammas(4) * cos(t123);
    QyOut = gammas(2) * sin(t1) + gammas(3) * sin(t12) + gammas(4) * sin(t123);

    fprintf('Section 4.2 equilibrium solve\n');
    fprintf('theta = [%.6f %.6f %.6f]\n', theta(1), theta(2), theta(3));
    fprintf('Q = [%.6f %.6f]\n', QxOut, QyOut);
    fprintf('tip slope = %.6f\n', t123);
end
