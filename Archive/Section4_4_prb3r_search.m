% Section 4.3 + 4.4 PRB 3R search from Haijun Su's paper.
%
% This is a script, not a function.
%
% What it does:
%   1. Generates pure-moment and pure-vertical-force beam states
%   2. Uses Section 4.3 to compute equivalent spring stiffness for a given
%      candidate set of characteristic radius factors
%   3. Uses Section 4.4 to search for the optimal gamma values by minimizing
%      the difference between pure-moment and pure-force stiffness values
%
% Default settings are chosen to match the report's test:
%   L / t = 100
%   sigma_max / E = 0.03
% which gives a large enough allowable slope range for the pure-moment fit.

clear;
clc;

% -------------------------------------------------------------------------
% User inputs
% -------------------------------------------------------------------------
lOverT = 100.0;
sigmaOverE = 0.03;

gammaStep = 0.05;
gammaMin = 0.05;
gammaMax = 0.50;

numMomentSamples = 80;
numForceSamples = 80;

forceAngle = pi / 2.0;  % vertical force load for Section 4.6

% -------------------------------------------------------------------------
% Stress-limit check from Section 2.2
% -------------------------------------------------------------------------
thetaStressLimit = 2.0 * lOverT * sigmaOverE;
thetaMomentMax = min(thetaStressLimit, 3.0 * pi / 2.0);
thetaForceMax = min(thetaStressLimit, pi / 2.0);

fprintf('Section 4.3 + 4.4 PRB 3R search\n');
fprintf('L/t = %.3f\n', lOverT);
fprintf('sigma_max / E = %.5f\n', sigmaOverE);
fprintf('theta stress limit = %.6f rad\n', thetaStressLimit);
fprintf('pure-moment fit range = [0, %.6f] rad\n', thetaMomentMax);
fprintf('pure-force fit range  = [0, %.6f] rad\n\n', thetaForceMax);

thetaMomentVals = linspace(1.0e-4, thetaMomentMax, numMomentSamples);
thetaForceVals = linspace(1.0e-4, thetaForceMax, numForceSamples);

bestObjective = inf;
bestGammas = [];
bestKbarMoment = [];
bestKbarForce = [];

gammaValues = gammaMin:gammaStep:gammaMax;

for gamma0 = gammaValues
    for gamma1 = gammaValues
        for gamma2 = gammaValues
            gamma3 = 1.0 - gamma0 - gamma1 - gamma2;

            if gamma3 < gammaMin - 1.0e-12 || gamma3 > gammaMax + 1.0e-12
                continue;
            end

            gamma3 = round(gamma3 / gammaStep) * gammaStep;
            if gamma3 < gammaMin - 1.0e-12 || gamma3 > gammaMax + 1.0e-12
                continue;
            end

            gammas = [gamma0; gamma1; gamma2; gamma3];

            if abs(sum(gammas) - 1.0) > 1.0e-12
                continue;
            end

            kbarMoment = fit_pure_moment_stiffness(gammas, thetaMomentVals);
            kbarForce = fit_pure_force_stiffness(gammas, thetaForceVals, forceAngle);
            objective = sum((kbarMoment - kbarForce).^2);

            if objective < bestObjective
                bestObjective = objective;
                bestGammas = gammas;
                bestKbarMoment = kbarMoment;
                bestKbarForce = kbarForce;
            end
        end
    end
end

fprintf('Best objective = %.8e\n', bestObjective);
fprintf('Optimal gammas = [%.2f %.2f %.2f %.2f]\n', ...
    bestGammas(1), bestGammas(2), bestGammas(3), bestGammas(4));
fprintf('Pure-moment kbar = [%.5f %.5f %.5f]\n', ...
    bestKbarMoment(1), bestKbarMoment(2), bestKbarMoment(3));
fprintf('Pure-force  kbar = [%.5f %.5f %.5f]\n', ...
    bestKbarForce(1), bestKbarForce(2), bestKbarForce(3));

fprintf('\nReport comparison targets:\n');
fprintf('Eq. (24): gammas = [0.10 0.35 0.40 0.15]\n');
fprintf('Eq. (25): pure-moment kbar = [3.51933 2.78518 2.79756]\n');
fprintf('Eq. (27): pure-force  kbar = [3.71591 2.87128 2.26417]\n');

% -------------------------------------------------------------------------
% Local functions
% -------------------------------------------------------------------------
function kbar = fit_pure_moment_stiffness(gammas, thetaVals)
    thetaPRB = zeros(3, numel(thetaVals));
    torquePRB = zeros(3, numel(thetaVals));

    for idx = 1:numel(thetaVals)
        theta0 = thetaVals(idx);
        qx = sin(theta0) / theta0;
        qy = (1.0 - cos(theta0)) / theta0;
        eta = theta0;

        theta = inverse_kinematics_prb3r(qx, qy, theta0, gammas, 'auto');
        J = prb3r_jacobian(theta, gammas);
        loadVec = [0.0; 0.0; eta];
        torque = J' * loadVec;

        thetaPRB(:, idx) = theta;
        torquePRB(:, idx) = torque;
    end

    kbar = zeros(3, 1);
    for j = 1:3
        kbar(j) = (thetaPRB(j, :) * torquePRB(j, :)') / (thetaPRB(j, :) * thetaPRB(j, :)');
    end
end

function kbar = fit_pure_force_stiffness(gammas, thetaVals, phi)
    thetaPRB = zeros(3, numel(thetaVals));
    torquePRB = zeros(3, numel(thetaVals));

    for idx = 1:numel(thetaVals)
        theta0 = thetaVals(idx);
        [lambda, qx, qy] = solve_section2_state(theta0, phi, 0.0);

        theta = inverse_kinematics_prb3r(qx, qy, theta0, gammas, 'auto');
        J = prb3r_jacobian(theta, gammas);
        loadVec = [2.0 * lambda * cos(phi); 2.0 * lambda * sin(phi); 0.0];
        torque = J' * loadVec;

        thetaPRB(:, idx) = theta;
        torquePRB(:, idx) = torque;
    end

    kbar = zeros(3, 1);
    for j = 1:3
        kbar(j) = (thetaPRB(j, :) * torquePRB(j, :)') / (thetaPRB(j, :) * thetaPRB(j, :)');
    end
end

function [lambda, qx, qy] = solve_section2_state(theta0, phi, kappa)
    u = linspace(0.0, 1.0, 4000);
    theta = theta0 * (2.0 * u - u .* u);
    dthetaDu = 2.0 * theta0 * (1.0 - u);

    rootArg = cos(theta0 - phi) - cos(theta - phi) + kappa;
    rootValues = sqrt(max(rootArg, 1.0e-12));

    I0 = trapz(u, (1.0 ./ rootValues) .* dthetaDu);
    Ix = trapz(u, (cos(theta) ./ rootValues) .* dthetaDu);
    Iy = trapz(u, (sin(theta) ./ rootValues) .* dthetaDu);

    lambda = 0.5 * I0;
    qx = Ix / (2.0 * lambda);
    qy = Iy / (2.0 * lambda);
end

function theta = inverse_kinematics_prb3r(qx, qy, theta0, gammas, elbowMode)
    px = qx - gammas(4) * cos(theta0) - gammas(1);
    py = qy - gammas(4) * sin(theta0);

    cosTheta2 = (px^2 + py^2 - gammas(2)^2 - gammas(3)^2) / (2.0 * gammas(2) * gammas(3));
    cosTheta2 = max(-1.0, min(1.0, cosTheta2));

    if strcmpi(elbowMode, 'auto')
        thetaDown = build_theta_from_sign(+1.0, px, py, theta0, gammas, cosTheta2);
        thetaUp = build_theta_from_sign(-1.0, px, py, theta0, gammas, cosTheta2);

        scoreDown = monotonic_branch_score(thetaDown, theta0);
        scoreUp = monotonic_branch_score(thetaUp, theta0);

        if scoreDown <= scoreUp
            theta = thetaDown;
        else
            theta = thetaUp;
        end
        return;
    elseif strcmpi(elbowMode, 'down')
        signValue = +1.0;
    else
        signValue = -1.0;
    end

    theta = build_theta_from_sign(signValue, px, py, theta0, gammas, cosTheta2);
end

function J = prb3r_jacobian(theta, gammas)
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
end

function theta = build_theta_from_sign(signValue, px, py, theta0, gammas, cosTheta2)
    theta2 = signValue * acos(cosTheta2);
    denom = gammas(2)^2 + gammas(3)^2 + 2.0 * gammas(2) * gammas(3) * cos(theta2);
    cosTheta1 = (px * (gammas(2) + gammas(3) * cos(theta2)) + py * gammas(3) * sin(theta2)) / denom;
    sinTheta1 = (py * (gammas(2) + gammas(3) * cos(theta2)) - px * gammas(3) * sin(theta2)) / denom;
    theta1 = atan2(sinTheta1, cosTheta1);
    theta3 = theta0 - theta1 - theta2;
    theta = [theta1; theta2; theta3];
end

function score = monotonic_branch_score(theta, theta0)
    desiredSign = sign(theta0);
    if desiredSign == 0
        desiredSign = 1.0;
    end

    wrongSignPenalty = sum(max(0.0, -desiredSign .* theta));
    reconstructionPenalty = abs(sum(theta) - theta0);
    score = wrongSignPenalty + 10.0 * reconstructionPenalty;
end
